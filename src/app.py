import sys
import subprocess
import pickle
from flask import Flask, render_template, request
# import finalnlp
import finaleval
import time

app = Flask(__name__)

# Path to a Python interpreter under the venv

python_bin = "../modelvenv/bin/python"
# python_bin = "C:\\Users\\sparsha\\modelvenv\\Scripts\\python"

# Path to the script that must run under the venv
script_file = "restorefinalmodel.py"

@app.route('/')
def index():
    return render_template('index.html', result = dict() , mapping = "")

@app.route('/', methods = ['POST'])
def upload():
    import finalnlp
    user_facts = request.form['insert_facts']
    user_questions = request.form['insert_questions']
    print(user_facts, user_questions)
    # query = "Mary went to school and John did not. If Mary and John went to school then Ram did not. Did Mary and Ram go to school? Did John not go to school?"

    start = time.time()
    nlp_output = finalnlp.NLP_main(' '.join([user_facts, user_questions]))
    end = time.time()
    print("time :", end-start)

    conditionals, facts, questions, predFacts, predQuest , nlp_question , list_question , nlp_list_question = nlp_output
    print()
    print("nlp_output : " , nlp_output)
    print()

    eval_input = [facts, list_question, predFacts, predQuest, nlp_question, nlp_list_question]
    if(questions):
        model_input = [conditionals,questions]
        data_comm = open('data.pkl', 'wb')
        pickle.dump(model_input, data_comm)
        data_comm.close()

        model = subprocess.Popen([python_bin, script_file])
        model.communicate()

        f2 = open('data.pkl', 'rb')
        model_output = pickle.load(f2)
        f2.close()
        print()
        print("model_output : " , model_output)
        print()

        eval_input.extend(model_output)

    else:
        eval_input.extend([conditionals , questions])

    print("EVAL" , eval_input)
    result = finaleval.eval_main(eval_input)

    print(nlp_output , model_output , result)

    # nlp_output = [[], ['a', 'b ^ c'], ['a'], {'a': 'go(mary,school)', 'b': 'eat(mary,cake)', 'c': 'eat(mary,bread)'}, {'a': 'go(mary,school)', 'e': 'eat(mary,x)'}, ['Did Mary go to school?'], ['e'], ['What did Mary eat?']]
    # eval_input = [['a', 'b ^ c'], ['e'], {'a': 'go(mary,school)', 'b': 'eat(mary,cake)', 'c': 'eat(mary,bread)'}, {'a': 'go(mary,school)', 'e': 'eat(mary,x)'}, ['Did Mary go to school?'], ['What did Mary eat?'], [], ['a']]
    # result = {'Did Mary and Ram go to the school?' : 'True'}
    return render_template('result.html', result = result, mapping = user_facts, nlp_output = nlp_output, eval_input = eval_input)

if __name__ == '__main__':
    app.run()
