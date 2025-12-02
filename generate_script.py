import os
# 适配新版 LangChain 的引用方式
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities import SerpAPIWrapper
from langchain_community.chat_models import ChatTongyi


def generate_script(subject, video_length, creativity, api_key, serpapi_api_key):
    """
    生成脚本的核心函数（调试模式版）
    去掉了所有 try...except，让错误直接暴露给主程序捕获
    """

    # 1. 基础检查
    if not api_key:
        raise ValueError("严重错误：generate_script 未接收到 api_key")
    if not serpapi_api_key:
        # SerpApi 如果没有，只打印警告，不阻断（这是唯一可以容忍的错误）
        print("⚠️ 警告：未接收到 SerpApi Key，搜索功能将失效")

    # 设置环境变量（某些底层库仍依赖这个）
    os.environ["DASHSCOPE_API_KEY"] = api_key
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

    # 3. 初始化模型 (这是最容易报错的地方)
    # 使用 'model' 参数，而非 'model_name' (新版规范)
    # 如果 qwen-max 报错，请尝试改成 qwen-turbo
    model = ChatTongyi(
        model="qwen-max",
        temperature=creativity,
        api_key=api_key
    )

    # 4. 生成标题 (如果不加 try，这里出错会直接抛出，app.py 会显示具体原因)
    print(f"📝 正在调用模型生成标题... (Key长度: {len(api_key)})")
    title_chain = title_template | model
    title_response = title_chain.invoke({"subject": subject})

    # 兼容性处理：有些版本返回对象，有些返回字符串
    if hasattr(title_response, 'content'):
        title = title_response.content.strip()
    else:
        title = str(title_response).strip()

    # 5. 网络搜索 (允许失败)
    search_results = "（因搜索失败，仅使用模型内置知识）"
    if serpapi_api_key:
        try:
            print("🌐 正在尝试搜索...")
            search = SerpAPIWrapper(serpapi_api_key=serpapi_api_key, params={"engine": "baidu"})
            # 尝试搜索，如果失败则捕获
            res = search.run(subject)
            if res:
                search_results = res
        except Exception as e:
            print(f"⚠️ 搜索步骤出错 (忽略): {e}")
            # 搜索失败不应该导致整个脚本生成失败
            search_results = f"搜索暂不可用: {str(e)}"

    # 6. 生成脚本
    print("✍️ 正在生成正文...")
    script_chain = script_template | model
    script_response = script_chain.invoke({
        "title": title,
        "duration": video_length,
        "search_result": search_results
    })

    if hasattr(script_response, 'content'):
        script = script_response.content.strip()
    else:
        script = str(script_response).strip()

    return search_results, title, script