import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os
from langchain_core.messages import AIMessage, HumanMessage

load_dotenv()

from langchain_openai import AzureChatOpenAI
model = AzureChatOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    temperature=0,
)

from io import BytesIO

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    processed_data = output.getvalue()
    return processed_data


def detect_anomalies_per_column(df, selected_columns, detection_rules):
    results = {}
    for column in selected_columns:
        texts = df[column].astype(str).tolist()
        rule = detection_rules.get(column, "")
        anomalies = []
        for text in texts:
           resp = model.invoke([
                AIMessage(content=f"""你是一名数据分析专家。请根据以下检测规则，判断给定的文本是否为异常值。请回答“是”或“否”。"""),
                HumanMessage(content=f"""
                检测规则：{rule} 
                文本：{text}""")
           ]);
           result = resp.content
           print(rule, text, result)
           anomalies.append(result)
        results[column] = anomalies
    return results

def process_file(df):
    st.subheader("数据预览（前 10 行）")
    st.dataframe(df.head(10))

    task = st.selectbox("请选择数据处理任务", ["脏数据检测", "语义情感分析", "数据可视化"])
    st.info('我昨天白天睡眼朦胧中想到：我们是不是有点 Workflow 的意思，可以选择上述不同的小任务编排后自动化处理 Excel 数据。', icon="ℹ️")

    if task == "脏数据检测":
        text_columns = df.select_dtypes(include=["object"]).columns.tolist()
        selected_columns = st.multiselect("请选择要处理的文本列（可多选）", text_columns)

        detection_rules = {}
        if selected_columns:
            st.subheader("为每个列设置检测规则")
            for column in selected_columns:
                with st.expander(f"设置列 {column} 的检测规则"):
                    rule = st.text_area(f"请输入 {column} 列的检测规则", key=f"rule_{column}")
                    detection_rules[column] = rule

            if st.button("开始检测"):
                if all(detection_rules.values()):
                    with st.spinner("正在进行脏数据检测，请稍候..."):
                        # 调用异常检测函数
                        anomaly_results = detect_anomalies_per_column(df, selected_columns, detection_rules)
                        # 将检测结果添加到数据框中
                        for column in selected_columns:
                            df[f"{column}_检测结果"] = anomaly_results[column]
                    st.subheader("检测结果（前 10 行）")
                    st.dataframe(df.head(10))

                    # 将 DataFrame 转换为 Excel 格式
                    excel_data = to_excel(df)

                    # 提供下载按钮导出数据
                    st.download_button(
                        label="下载检测结果 Excel 文件",
                        data=excel_data,
                        file_name='检测结果.xlsx',
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
        else:
            st.warning("请先选择要处理的文本列。")
    else:
        st.warning("尚未实现该功能。")





st.title("增长汪汪 - BI 数据分析工具")

uploaded_file = st.file_uploader("请选择一个 Excel 文件", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    st.success("文件上传成功！")
    process_file(df)
else:
    st.warning("请先上传一个 Excel 文件。")