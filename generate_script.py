import os
# 改为从 core 引入
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities import SerpAPIWrapper  # 使用 SerpApi 进行网络搜索
from langchain_community.chat_models import ChatTongyi


def generate_script(subject, video_length, creativity, api_key, serpapi_api_key):
    """
    使用阿里云通义千问生成短视频脚本，并结合百度搜索补充背景知识
    """
    print("🚀 开始生成脚本...")
    print(f"🔍 主题: {subject}, 时长: {video_length}分钟, 创意度: {creativity}")

    # 【重要】确保 Key 不为空，如果为空直接报错，方便调试
    if not api_key:
        print("❌ 错误：未接收到阿里云 API Key")
        return None, None, None
    if not serpapi_api_key:
        print("❌ 错误：未接收到 SerpApi Key")
        return None, None, None

    # 设置环境变量（为了 SerpApi 和 DashScope 的底层调用）
    os.environ["DASHSCOPE_API_KEY"] = api_key
    os.environ["SERPAPI_API_KEY"] = serpapi_api_key

    # 1. 标题生成模板
    title_template = ChatPromptTemplate.from_messages(
        [
            ("human", "请为'{subject}'这个主题的视频写一个吸引人的中文标题，只输出标题内容。")
        ]
    )

    # 2. 脚本生成模板
    script_template = ChatPromptTemplate.from_messages(
        [
            (
                "human",
                """你是一位爆款短视频博主，请根据以下信息写一个视频脚本。
                 视频标题：{title}
                 视频时长：{duration}分钟
                 要求：
                 - 开头3秒必须抓眼球（悬念/冲突/反常识）
                 - 中间提供干货或有趣知识
                 - 结尾有反转或彩蛋
                 - 表达轻松幽默，适合年轻人
                 - 总长度适配时长

                 可参考以下网络搜索信息（仅提取相关部分）：
                 {search_result}

                 请按以下格式输出：
                 【开头】
                 ...
                 【中间】
                 ...
                 【结尾】
                 ..."""
            )
        ]
    )

    # 3. 初始化通义千问模型
    # 【修改点】注意这里的参数变化，最新版通常使用 model
    try:
        model = ChatTongyi(
            model="qwen-max",  # 将 model_name 改为 model
            temperature=creativity,
            api_key=api_key  # 显式传入 api_key
        )
    except Exception as e:
        print(f"❌ 模型初始化失败: {e}")
        return None, None, None

    # 构建链
    title_chain = title_template | model
    script_chain = script_template | model

    # 4. 生成标题
    print("📝 正在生成标题...")
    try:
        title_response = title_chain.invoke({"subject": subject})
        # 兼容不同版本的返回结构（有时候返回是 string，有时候是 message 对象）
        if hasattr(title_response, 'content'):
            title = title_response.content.strip()
        else:
            title = str(title_response).strip()

        print(f"✅ 标题生成完成：{title}")
    except Exception as e:
        print(f"❌ 标题生成失败详细报错：{e}")
        # 这里不要直接 return，方便我们看是不是只有标题挂了
        return None, None, None

    # 5. 使用 SerpApi 进行百度搜索（中文）
    print("🌐 正在进行网络搜索（百度）...")
    try:
        search = SerpAPIWrapper(
            serpapi_api_key=serpapi_api_key,
            params={"engine": "baidu"}  # 某些版本需要这样传 engine
        )
        search_results = search.run(subject)
        print(f"📄 搜索成功")
    except Exception as e:
        print(f"⚠️ 网络搜索失败（非阻断性错误）：{e}")
        search_results = "未找到相关网络资料。"

    # 6. 生成脚本
    print("✍️ 正在生成视频脚本...")
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

        print("🎬 脚本生成完成！")
        return search_results, title, script
    except Exception as e:
        print(f"❌ 脚本生成失败：{e}")
        return search_results, title, None