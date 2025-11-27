# app.py - AI短视频脚本生成器（最终版）
# 支持：左侧参数栏 | API Key 可选覆盖 | 环境变量自动读取 | 用户友好提示

import streamlit as st
from generate_script import generate_script
import os

# =================== 从环境变量读取后端密钥 ===================
DASHSCOPE_DEFAULT_KEY = os.getenv("DASHSCOPE_API_KEY")  # 默认Key来自环境变量
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")           # 必须存在！

if not SERPAPI_API_KEY:
    st.error("❌ 后端错误：未检测到 SERPAPI_API_KEY 环境变量，请联系管理员设置。")
    st.stop()

# 设置页面
st.set_page_config(
    page_title="🎬 AI短视频脚本生成器",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        "输入你的 DashScope API Key",
        type="password",
        placeholder="以 sk- 开头（留空则使用系统默认）"
    )

    # 显示当前使用的 Key 来源
    final_api_key = user_api_key or DASHSCOPE_DEFAULT_KEY

    if not final_api_key:
        st.warning("⚠️ 未提供任何阿里云 API Key，无法生成内容。")
        valid_api = False
    elif not final_api_key.startswith("sk-"):
        st.error("❌ 提供的 API Key 格式无效。")
        valid_api = False
    else:
        masked = f"{final_api_key[:6]}...{final_api_key[-4:]}"
        st.info(f"✅ 使用 Key: `{masked}`")
        valid_api = True

    # --- 获取链接 ---
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
        with st.spinner("🧠 AI正在思考标题... 🔍 搜索资料... ✍️ 生成脚本..."):
            search_results, title, script = generate_script(
                subject=subject,
                video_length=video_length,
                creativity=creativity,
                api_key=final_api_key,
                serpapi_api_key=SERPAPI_API_KEY  # 完全由后台管理
            )

        if script:
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

            # 展开查看参考资料
            with st.expander("🔍 查看网络搜索参考（用于知识增强）"):
                st.write(search_results)

            # 下载功能
            full_content = f"""# AI短视频脚本
【主题】 {subject}
【时长】 {video_length} 分钟
【创意度】 {creativity}

---
## 标题：
{title}

## 脚本：
{script}

---
参考资料：
{search_results}
"""
            st.download_button(
                label="📥 下载文本文件",
                data=full_content,
                file_name=f"短视频脚本_{subject}_{int(st.session_state.get('count',0)+1)}.txt",
                mime="text/plain"
            )

            # 记录历史
            if 'count' not in st.session_state:
                st.session_state.count = 0
            st.session_state.count += 1

            st.session_state.history.append({
                "subject": subject,
                "title": title,
                "preview": script[:100] + "..." if len(script) > 100 else script
            })

# =============== 历史记录面板 ===============
st.divider()
st.markdown("### 🕰️ 最近生成记录")
if st.session_state.history:
    for idx, item in enumerate(reversed(st.session_state.history)):
        with st.expander(f"`{idx+1}` {item['subject']} → _{item['title']}_"):
            st.write(item["preview"])
else:
    st.markdown("<p style='color: gray;'>暂无生成记录</p>", unsafe_allow_html=True)
