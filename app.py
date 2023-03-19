import os
from flask import Flask, request, jsonify, send_from_directory
import openai
import pandas as pd

app = Flask(__name__)

@app.route('/api/generate_answers', methods=['POST'])
def generate_answers():
    data = request.get_json()
    questionnaire = data.get('questionnaire')

    # 处理问卷内容
    # ...

    # 与OpenAI API交互并获取回答
    answers = []
    for i in range(20):
        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=questionnaire,
        temperature=0.7,
        max_tokens=100,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )
    answer = response.choices[0].text.strip()
    answers.append(answer)

# 将回答数据转换为Excel表格并存储
df = pd.DataFrame(answers, columns=["Answer"])
df.to_excel("generated_answers.xlsx", index=False)

return jsonify({"success": True})
# 运行Flask应用
app.run(host='0.0.0.0', port=8080, debug=True)

@app.route('/api/download_excel', methods=['GET'])
def download_excel():
try:
return send_from_directory(
os.path.abspath('.'), "generated_answers.xlsx", as_attachment=True
)
except FileNotFoundError:
abort(404)

if name == 'main':
# 设置OpenAI API密钥
openai.api_key = "your_openai_api_key"
