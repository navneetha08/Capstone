import sys
import subprocess
import pickle
from flask import Flask, render_template, request
import finalnlp
import finaleval
import time

app = Flask(__name__)

# Path to a Python interpreter under the venv
python_bin = "../modelvenv/bin/python"

# Path to the script that must run under the venv
script_file = "restorefinalmodel.py"

@app.route('/')
def index():
    return render_template('index.html', result = dict() , mapping = "" )

@app.route('/', methods = ['POST'])
def upload():
    user_query = request.form['insert_query']
    #query = "Mary went to school and John did not. If Mary and John went to school then ram did not. Did mary and ram go to school? Did John not go to school?"

    # result = 'Hello ' + name

    start = time.time()
    nlp_output = finalnlp.NLP_main(user_query)
    end = time.time()
    print("time :", end-start)

    conditionals, facts, questions, predFacts, predQuest , nlp_question = nlp_output
    print()
    print("nlp_output : " , nlp_output)
    print()

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

    model_output.append(facts)

    result = finaleval.eval_main(model_output , nlp_question)

    # print(nlp_output , model_output , result)
    return render_template('index.html', result = result, mapping = user_query)

if __name__ == '__main__':
    app.run(debug = True)
