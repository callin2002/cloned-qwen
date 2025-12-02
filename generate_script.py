import os
import streamlit as st  # 引入 streamlit 以便直接在网页上打印调试信息
# 适配新版 LangChain 的引用方式
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities import SerpAPIWrapper
from langchain_community.chat_models import ChatTongyi


def generate_script(subject, video_length, creativity, api_key, serpapi_api_key):
    """
    超级调试版：直接将运行进度打印到 Streamlit 网页上
    """
    st.info("🔍 DEBUG: 已进入 generate_script 函数内部")

    # 1. 基础检查
    if not api_key:
        st.error("❌ DEBUG: api_key 为空！")
        raise ValueError("严重错误：generate_script 未接收到 api_key")
    else:
        st.write(f"✅ DEBUG: 接收到 API Key，长度: {len(str(api_key))}")

    # 设置环境变量
    os.environ["DASHSCOPE_API_KEY"] = api_key
    if serpapi_api_key:
        os.environ["SERPAPI_API_KEY"] = serpapi_api_key

    # 2. 定义 Prompt 模板
    title_template = ChatPromptTemplate.from_messages([
        ("human", "请为'{subject}'这个主题的视频写一个吸引人的中文标题，只输出标题内容，不要包含任何解释或引号。")
    ])

    script_template = ChatPromptTemplate.from_messages([
        ("human", """你是一位爆款短视频博主。
        视频标题：{title}
        视频时长：{duration}分钟
        参考资料：{search_result}

        请写一个脚本，包含【开头】【中间】【结尾】。
        要求：开头3秒抓人眼球，语言口语化，适合快节奏剪辑。""")
    ])

    # 3. 初始化模型
    st.write("🤖 DEBUG: 正在初始化 ChatTongyi 模型...")
    try:
        # 尝试使用 qwen-turbo，因为 qwen-max 有时候需要额外权限或更贵
        model = ChatTongyi(
            model="qwen-turbo",
            temperature=creativity,
            api_key=api_key
        )
        st.write("✅ DEBUG: 模型初始化成功")
    except Exception as e:
        st.error(f"❌ DEBUG: 模型初始化失败: {e}")
        raise e

    # 4. 生成标题
    st.write("📝 DEBUG: 正在调用模型生成标题...")
    title_chain = title_template | model

    try:
        title_response = title_chain.invoke({"subject": subject})
        # 兼容性处理
        if hasattr(title_response, 'content'):
            title = title_response.content.strip()
        else:
            title = str(title_response).strip()
        st.write(f"✅ DEBUG: 标题生成成功: {title}")
    except Exception as e:
        st.error(f"❌ DEBUG: 标题生成崩溃: {e}")
        raise e

    # 5. 网络搜索
    search_results = "（因搜索失败，仅使用模型内置知识）"
    if serpapi_api_key:
        st.write("🌐 DEBUG: 正在尝试网络搜索...")
        try:
            search = SerpAPIWrapper(serpapi_api_key=serpapi_api_key, params={"engine": "baidu"})
            res = search.run(subject)
            if res:
                search_results = res
                st.write("✅ DEBUG: 搜索成功")
            else:
                st.write("⚠️ DEBUG: 搜索返回为空")
        except Exception as e:
            st.warning(f"⚠️ DEBUG: 搜索出错 (已忽略): {e}")

    # 6. 生成脚本
    st.write("✍️ DEBUG: 正在生成最终脚本...")
    script_chain = script_template | model

    try:
        script_response = script_chain.invoke({
            "title": title,
            "duration": video_length,
            "search_result": search_results
        })

        if hasattr(script_response, 'content'):
            script = script_response.content.strip()
        else:
            script = str(script_response).strip()

        st.write("✅ DEBUG: 脚本生成完成！准备返回数据。")
    except Exception as e:
        st.error(f"❌ DEBUG: 脚本生成崩溃: {e}")
        raise e

    # 这里的 return 绝对不可能返回 None，除非前面报错被 raise 了
    return search_results, title, script