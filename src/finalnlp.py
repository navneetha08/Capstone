import nltk
import benepar
import spacy
from benepar.spacy_plugin import BeneparComponent
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize

# nltk.download("stopwords")
# nltk.download("punkt")
# nltk.download('wordnet')

benepar.download('benepar_en2')
nlp = spacy.load('en_core_web_sm')
nlp.add_pipe(BeneparComponent('benepar_en2'))

stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

def split_sentence(text, op, letter, sentences, sen, flags, pred):
  doc = nlp(text)
  sent = list(doc.sents)[0]
  string = sent._.parse_string
  string = string.replace("(", "")
  string = string.replace(")", "")
  string = string.split()
  # print(string)

  pred[letter].append({})
  part = ""
  i = 0
  n = len(string)
  temp_owner = ""

  while(i < n):
      if(string[i] == 'NP' and flags['NP'] == 0):
        # flags['NP'] = 1
        while(i < n and string[i] != 'VP'):
          if(string[i] in sentences[sen] and (string[i] != '.' and string[i] != '?')):
            part += string[i] + ' '
          i += 1
        pred[letter][1]['N'] = part.strip()
        if(i < n):
          flags['NP'] = 1
        part = ""

      elif(string[i] == 'VP' and flags['VP'] == 0):
        flags['VP'] = 1
        while(i < n):
          if(string[i].startswith("VB")):
            pred[letter][1]['V'] = string[i + 1]
            i += 2
            break
          else:
            i += 1
        while(i < n and string[i] != 'PP'):
          if(string[i] in sentences[sen] and (string[i] != '.' and string[i] != '?')):
            part += string[i] + ' '
          if(string[i] == 'NNP'):
            temp_owner = string[i + 1]
            i += 1
          i += 1
        part += temp_owner
        if(part):
          pred[letter][1]['AV'] = part.strip()
        part = ""

      elif(string[i] == 'PP'):
        while(i < n):
          if(string[i] in sentences[sen] and (string[i] != '.' and string[i] != '?')):
            part += string[i] + ' '
          i += 1
        if(part):
          pred[letter][1]['P'] = part.strip()
        flags['NP'] = flags['VP'] = flags['PP'] = 0
        part = ""

      elif(flags['VP']):
        while(i < n and string[i] != 'PP'):
          if(string[i] in sentences[sen] and (string[i] != '.' and string[i] != '?')):
            part += string[i] + ' '
          if(string[i] == 'NNP'):
            temp_owner = string[i + 1]
            i += 1
          i += 1
        part += temp_owner
        if(part):
          pred[letter][1]['AV'] = part.strip()
        part = ""

      else:
        i += 1

  return text

def parameterize(question):
  func_info = dict()
  for letter in question.keys():
    temp_args = list()
    for part in ['N', 'AV', 'P']:
      if(part in question[letter][1]):
        for w in question[letter][1][part].split():
          if w not in stop_words:
            temp_args.append(lemmatizer.lemmatize(str.lower(w)))
    func_info[letter] = lemmatizer.lemmatize(question[letter][1]['V'] , 'v') + "(" + ",".join(temp_args) + ")"
  question.clear()
  question.update(func_info)

def process_question(statement, op, letters, sen, sentences, flags, predQues, questions, nlp_questions, list_questions, nlp_list_questions):
  ques = ""
  expression = ""
  terms = statement.split()
  check = True

  first_word = str.lower(terms.pop(0))
  if(lemmatizer.lemmatize(str.lower(terms[0]), 'v') == "do"):
    terms.pop(0)
  if(first_word == "where" or first_word == "what"):
    check = False
    terms[-1] = terms[-1].replace("?", " x?")
  elif(first_word == "who"):
    check = False
    terms.insert(0, "x")

  if(check):
    nlp_questions.append(statement)
  else:
    nlp_list_questions.append(statement)

  statement = " ".join(terms)

  for term in word_tokenize(statement):
    if(term not in op and term != "?"):
      ques += term + ' '
    else:
      # print("ques:", ques)
      ques = ques.strip()
      letter = letters.pop(0)
      predQues[letter] = list()
      predQues[letter].append(ques)

      if("not" in ques):
        expression += '~ '
        # print("~" , end=" ")
        l = ques.split()
        ind = l.index("not")
        l.pop(ind)
        ques = " ".join(l)

      if(term == '?'):
        ques += term
        expression += letter + ' '
        # print(letter, end = " ")
        if(check):
          questions.append(expression.strip())
        else:
          list_questions.append(expression.strip())
        expression = ""
        # print()
      else:
        expression += letter + ' ' + op[term] + ' '
        # print(letter, op[term], end = " ")

      predQues[letter][0] = ques
      sentences[sen] = ques
      split_sentence(ques, op, letter, sentences, sen, flags, predQues)
      ques = ""

def process_fact(statement, op, letters, sen, sentences, flags, expression, predFacts, allFacts):
  text = ""
  for term in word_tokenize(statement):
    if (term not in op):
      if (term != "if"):
        text += term + ' '
    else:
      # print("op", term)
      text = text.strip()
      letter = letters.pop(0)
      if("not" in text):
        expression += '~ '
        # print("~" , end=" ")
        l = text.split()
        ind = l.index("not")
        l.pop(ind)
        l.pop(ind-1)
        text = " ".join(l)

      if(term == '.'):
        text += term
        expression += letter + ' '
        # print(letter, end = " ")
        allFacts.append(expression.strip())
        expression = ""
        # print()
      else:
        expression += letter + ' ' + op[term] + ' '
        # print(letter, op[term], end = " ")

      predFacts[letter] = list()
      predFacts[letter].append(text)
      string = split_sentence(text, op, letter, sentences, sen, flags, predFacts)
      text = ""

def process_query(query, op, letters, predFacts = dict(), predQues = dict(), allFacts = list(), questions = list(), nlp_questions = list(), list_questions = list(), nlp_list_questions = list()):
  flags = {'NP' : 0, 'VP' : 0, 'PP' : 0}
  sentences = []
  sen = 0
  expression = ""

  tokenized = sent_tokenize(query)
  # print(tokenized)

  for statement in tokenized:
    # print(statement)
    sentences.append(statement)
    if("?" in statement):
      process_question(statement, op, letters, sen, sentences, flags, predQues, questions, nlp_questions, list_questions, nlp_list_questions)
    else:
      process_fact(statement, op, letters, sen, sentences, flags, expression, predFacts, allFacts)
    flags['NP'] = flags['VP'] = flags['PP'] = 0
    sen += 1

  # resolve conjunctions and merge parts of sentences
  resolve_conjunction(predFacts, '.')
  resolve_conjunction(predQues, '?')

def resolve_conjunction(info, delim):
  no_parts = {'N' : [] , 'V' : [] , 'AV' : [] , 'P' : [] }
  yes_parts = {'N' : [] , 'V' : [] , 'AV' : [] , 'P' : [] }

  letter_count = 0
  for letter in info.keys():
    letter_count += 1
    for part in no_parts.keys():
      if(part not in info[letter][1]):
        no_parts[part].append(letter)
      else:
        yes_parts[part].append(letter)
    if(info[letter][0][-1] == delim):
      # print(letter_count,no_parts, yes_parts)
      for part in no_parts.keys():
        if (len(no_parts[part]) < letter_count and len(yes_parts[part]) < letter_count):
            # print(part)
            for ele in no_parts[part]:
              ele_to_merge = yes_parts[part][0]
              info[ele][1][part] = info[ele_to_merge][1][part]
      no_parts = {'N' : [] , 'V' : [] , 'AV' : [] , 'P' : [] }
      yes_parts = {'N' : [] , 'V' : [] , 'AV' : [] , 'P' : [] }
      letter_count = 0

  for letter in info.keys():
    temp_text = ""
    for part in no_parts.keys():
      if(part in info[letter][1]):
        temp_text += info[letter][1][part] + ' '
    info[letter][0] = temp_text.strip()

def map_var(questions, facts, expressions):
  mapped_questions = dict()
  rev_facts = {v:k for k, v in facts.items()}

  for var in questions:
    param = questions[var]
    if param in rev_facts:
      mapped_questions[rev_facts[param]] = param
      for i in range(len(expressions)):
        if var in expressions[i]:
          expressions[i] = expressions[i].replace(var , rev_facts[param])
    else:
      mapped_questions[var] = param

  questions.clear()
  questions.update(mapped_questions)

def split_facts(allFacts):
  conditionals = list()
  facts = list()
  for expr in allFacts:
    if ('-' in expr):
      conditionals.append(expr)
    else:
      facts.append(expr)
  return [conditionals , facts]

def user_input(user_query):
  op = {'and' : '^', 'or' : 'v', '.' : '.' , 'then' : '-' }
  letters = [chr(x) for x in range(ord('a'), ord('z') + 1)]

  allFacts = list()
  questions = list()
  predFacts = dict()
  predQues = dict()
  nlp_questions = list()
  list_questions = list()
  nlp_list_questions = list()

  process_query(user_query, op, letters, predFacts, predQues, allFacts, questions , nlp_questions, list_questions, nlp_list_questions)
  parameterize(predFacts)
  parameterize(predQues)
  map_var(predFacts, predFacts, allFacts)
  map_var(predQues, predFacts, questions)
  return [allFacts, questions, predFacts, predQues, nlp_questions, list_questions, nlp_list_questions]

def NLP_main(user_query):
  allFacts, questions, predFacts, predQues, nlp_questions, list_questions, nlp_list_questions = user_input(user_query)
  conditionals, facts = split_facts(allFacts)
  print("Boolean Expressions:")
  print("Facts: " , allFacts)
  print("Questions: " , questions)
  print("NLP membership questions: ", nlp_list_questions)
  print("NLP questions: ", nlp_questions)
  print("List Questions: ", list_questions)
  print("Predicate Representation:")
  print("Facts: ", predFacts)
  print("Question: ", predQues)
  return [conditionals, facts, questions, predFacts, predQues, nlp_questions, list_questions, nlp_list_questions]
