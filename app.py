# app.py - AI短视频脚本生成器（修复版）
# 修复了：1. os.getenv 读不到 Key 的问题 2. 生成失败时网页无反应的问题

import streamlit as st
# 注意：这里不需要 import ChatTongyi，因为是在 generate_script.py 里调用的
from generate_script import generate_script
import os

# 设置页面 (必须是第一个 Streamlit 命令)
st.set_page_config(
    page_title="🎬 AI短视频脚本生成器",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =================== 核心修复 1：从 Secrets 读取密钥 ===================
# Streamlit Cloud 中，os.getenv 往往读不到，必须用 st.secrets
# 使用 .get() 防止本地运行时报错
try:
    DASHSCOPE_DEFAULT_KEY = st.secrets.get("DASHSCOPE_API_KEY", "")
    SERPAPI_API_KEY = st.secrets.get("SERPAPI_API_KEY", "")
except FileNotFoundError:
    # 本地没有 secrets.toml 时的兼容处理
    DASHSCOPE_DEFAULT_KEY = os.getenv("DASHSCOPE_API_KEY", "")
    SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")

# 检查后端必须的 Key
if not SERPAPI_API_KEY:
    st.error("❌ 配置错误：未检测到 `SERPAPI_API_KEY`。请在 Streamlit Cloud 后台 Secrets 中配置。")
    st.info("提示：如果是本地运行，请确保 secrets.toml 文件存在。")
    st.stop()

# =============== 左侧边栏：参数设置 ===============
with st.sidebar:
    st.title("🔧 参数设置")

    # --- 视频主题 ---
    subject = st.text_input("视频主题", placeholder="例如：Sora模型、多巴胺穿搭、AI绘画")

    # --- 视频时长 ---
    video_length = st.slider("视频时长（分钟）", min_value=0.5, max_value=3.0, step=0.5, value=1.0)

    # --- 创意度 ---
    creativity = st.slider(
        "创意度（Temperature）",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        help="数值越高越有创意，但可能偏离事实"
    )

    # --- 用户自定义 API Key（可选）---
    st.divider()
    st.markdown("### 🔐 阿里云 API 密钥（可选）")

    user_api_key = st.text_input(
        "输入 DashScope API Key",
        type="password",
        placeholder="sk-开头 (留空则用系统默认)"
    )

    # 逻辑：优先用用户输入的，没有则用系统配置的
    final_api_key = user_api_key.strip() or DASHSCOPE_DEFAULT_KEY

    # 状态指示灯
    valid_api = False
    if not final_api_key:
        st.warning("⚠️ 未检测到阿里云 API Key，无法运行。")
    elif not final_api_key.startswith("sk-"):
        st.error("❌ Key 格式错误：必须以 sk- 开头")
    else:
        st.success(f"✅ API Key 就绪 (末四位: {final_api_key[-4:]})")
        valid_api = True

    st.markdown("🔗 [获取 DashScope API Key](https://dashscope.aliyun.com/)")

# =============== 主区域：输出结果 ===============
st.title("🎯 AI短视频脚本生成器")
st.markdown("基于 **通义千问 + 实时网络搜索** 自动生成爆款短视频文案")

# 初始化历史记录
if 'history' not in st.session_state:
    st.session_state.history = []

# 生成按钮
if st.button("✨ 一键生成脚本", type="primary", disabled=not valid_api):
    if not subject.strip():
        st.error("请先输入视频主题！")
    else:
        # 显示加载状态
        with st.spinner("🚀 正在启动 AI 引擎... (可能需要 10-20 秒)"):

            # 调试信息：让用户知道程序真的在跑
            status_box = st.empty()
            status_box.info(f"正在处理主题：{subject}...")

            # 调用核心函数
            # 注意：generate_script 内部会把 Key 注入 os.environ
            try:
                search_results, title, script = generate_script(
                    subject=subject,
                    video_length=video_length,
                    creativity=creativity,
                    api_key=final_api_key,
                    serpapi_api_key=SERPAPI_API_KEY
                )
            except Exception as e:
                status_box.error(f"调用函数时发生未知崩溃: {e}")
                search_results, title, script = None, None, None

        # =================== 核心修复 2：处理失败情况 ===================
        # 之前的代码如果 script 是 None，什么都不做，导致页面无反应
        if script:
            status_box.empty()  # 清除进度提示
            st.success("✅ 脚本生成成功！")

            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown("### 📌 视频标题")
                st.markdown(f"<h4 style='color:#1f77b4;'>{title}</h4>", unsafe_allow_html=True)
            with col2:
                st.markdown("### ⏱️ 时长")
                st.metric(label="预计播放时间", value=f"{video_length} 分钟")

            st.markdown("---")
            st.markdown("### 📜 脚本正文")
            st.markdown(
                script.replace("\n", "<br>"),
                unsafe_allow_html=True
            )

            with st.expander("🔍 查看网络搜索参考资料"):
                st.write(search_results)

            # 下载和历史记录代码...
            full_content = f"# 视频脚本: {title}\n\n{script}\n\n参考:\n{search_results}"
            st.download_button(
                "📥 下载脚本",
                full_content,
                f"script_{subject}.txt"
            )

            # 存入历史
            st.session_state.history.append({"title": title, "preview": script[:50] + "..."})

        else:
            # 这就是之前缺失的部分！！！
            status_box.empty()
            st.error("❌ 生成失败！")
            st.error("原因：generate_script 函数返回了空值。")
            st.warning("👉 请点击右下角 'Manage app' 查看黑色控制台中的详细报错信息。")

            # 尝试给出常见建议
            st.info(
                "常见排查建议：\n1. 检查阿里云 Key 是否欠费或过期。\n2. 检查 SerpApi Key 是否有效。\n3. 检查 Streamlit Cloud 的 Secrets 是否填错了位置。")

# =============== 历史记录 ===============
st.divider()
st.markdown("### 🕰️ 最近记录")
if st.session_state.history:
    for item in reversed(st.session_state.history):
        st.text(f"📄 {item['title']}")
else:
    st.caption("暂无记录")