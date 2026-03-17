import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 数据库预设 ---
PROFILES = {
    "2020型": {"width": 20, "max_load_kg": 50, "price_per_m": 12},
    "3030型": {"width": 30, "max_load_kg": 150, "price_per_m": 25},
    "4040型": {"width": 40, "max_load_kg": 300, "price_per_m": 45},
}

PANELS = {
    "实木拼板 (18mm)": {"price_per_sqm": 200, "desc": "美观，适合做桌面或高端书架"},
    "亚克力板 (5mm)": {"price_per_sqm": 150, "desc": "透明，适合做防尘罩、轻型展示架"},
    "密度板/免漆板 (15mm)": {"price_per_sqm": 80, "desc": "性价比高，最适合做多层储物架"},
}

def draw_3d_frame(L, W, H, tiers, furniture_type):
    """使用 Plotly 绘制动态 3D 线框框架"""
    fig = go.Figure()
    
    # 画4根立柱
    columns = [
        ([0, 0], [0, 0], [0, H]), ([L, L], [0, 0], [0, H]),
        ([L, L], [W, W], [0, H]), ([0, 0], [W, W], [0, H])
    ]
    for x, y, z in columns:
        fig.add_trace(go.Scatter3d(x=x, y=y, z=z, mode='lines', line=dict(color='#7f8c8d', width=6), showlegend=False))
    
    # 计算每一层的高度 (Z轴)
    if furniture_type == "多层置物架":
        # 如果是多层，底层通常离地有一点距离，这里简化为从底到顶均分
        z_levels = [H * i / (tiers - 1) for i in range(tiers)] if tiers > 1 else [H]
    elif furniture_type == "简易四方箱体":
        z_levels = [0, H]
    else: # 基础桌子
        z_levels = [H]

    # 画每一层的横梁圈
    for z in z_levels:
        x_rect = [0, L, L, 0, 0]
        y_rect = [0, 0, W, W, 0]
        z_rect = [z, z, z, z, z]
        fig.add_trace(go.Scatter3d(
            x=x_rect, y=y_rect, z=z_rect,
            mode='lines', line=dict(color='#3498db', width=6),
            name=f"高度 {int(z)}mm 层"
        ))
    
    fig.update_layout(
        scene=dict(
            xaxis_title='长 (X)', yaxis_title='宽 (Y)', zaxis_title='高 (Z)',
            aspectmode='data'
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        height=450,
        showlegend=False
    )
    return fig

# --- 界面布局 ---
st.set_page_config(page_title="铝型材家具设计助手", layout="wide")
st.title("🧰 DIY 铝型材家具设计助手 (多层升级版)")
st.markdown("通过输入目标尺寸和层数，自动计算实际切割长度、配件数量，并生成采购清单 (BOM)。")

# 侧边栏：参数输入
with st.sidebar:
    st.header("1. 设定家具参数")
    furniture_type = st.selectbox("家具类型", ["多层置物架", "基础桌子/工作台", "简易四方箱体"])
    
    st.subheader("外部总尺寸 (毫米/mm)")
    L = st.number_input("长度 (Length)", min_value=100, max_value=3000, value=1000, step=10)
    W = st.number_input("宽度 (Width)", min_value=100, max_value=2000, value=400, step=10)
    H = st.number_input("高度 (Height)", min_value=100, max_value=2500, value=1500, step=10)
    
    tiers = 1
    if furniture_type == "多层置物架":
        tiers = st.number_input("层架数量 (包含顶层和底层)", min_value=2, max_value=10, value=4, step=1)
    
    st.header("2. 选择材料")
    profile_choice = st.selectbox("铝型材型号", list(PROFILES.keys()), index=1) # 置物架默认3030性价比高
    panel_choice = st.selectbox("面板材质", list(PANELS.keys()), index=2) # 默认选密度板

# --- 后台逻辑计算 ---
profile_w = PROFILES[profile_choice]["width"]
bom_items = []

# 1. 计算立柱 (4根顶到底)
bom_items.append({"配件类别": "框架型材", "配件名称": f"立柱 - {profile_choice}", "规格/尺寸": f"{H} mm", "数量": 4, "用途": "主框架立柱"})

# 2. 计算横梁与层板
# 横梁长度需要扣除两端立柱的厚度
l_len = L - (profile_w * 2)
w_len = W - (profile_w * 2)

if furniture_type == "多层置物架":
    l_qty = 2 * tiers
    w_qty = 2 * tiers
    panel_qty = tiers
    # 每层4个角，每个角需要2个角件（分别连接长宽横梁到立柱）
    bracket_qty = 8 * tiers 
elif furniture_type == "简易四方箱体":
    l_qty, w_qty, panel_qty, bracket_qty = 4, 4, 2, 16
else: # 桌子
    l_qty, w_qty, panel_qty, bracket_qty = 2, 2, 1, 8

bom_items.append({"配件类别": "框架型材", "配件名称": f"长横梁 - {profile_choice}", "规格/尺寸": f"{l_len} mm", "数量": l_qty, "用途": "长边支撑"})
bom_items.append({"配件类别": "框架型材", "配件名称": f"宽横梁 - {profile_choice}", "规格/尺寸": f"{w_len} mm", "数量": w_qty, "用途": "宽边支撑"})
bom_items.append({"配件类别": "层板物料", "配件名称": f"层板 ({panel_choice})", "规格/尺寸": f"{L}mm x {W}mm", "数量": panel_qty, "用途": "置物承重面"})

# 3. 计算连接件 (角件、螺栓、螺母)
# 一个角件通常配 2个螺栓 和 2个T型螺母
bom_items.append({"配件类别": "五金连接件", "配件名称": f"{profile_choice} 直角角件", "规格/尺寸": "标准", "数量": bracket_qty, "用途": "直角框架固定"})
bom_items.append({"配件类别": "五金连接件", "配件名称": "内六角螺栓", "规格/尺寸": "配套尺寸", "数量": bracket_qty * 2, "用途": "配合角件"})
bom_items.append({"配件类别": "五金连接件", "配件名称": "T型螺母 (滑块)", "规格/尺寸": "配套槽宽", "数量": bracket_qty * 2, "用途": "卡入型材槽内"})

# 可选附加件
bom_items.append({"配件类别": "附加件", "配件名称": "塑料端盖", "规格/尺寸": profile_choice, "数量": 4, "用途": "封建立柱顶部防刮"})
bom_items.append({"配件类别": "附加件", "配件名称": "调节地脚 / 承重万向轮", "规格/尺寸": "M8/M6螺纹", "数量": 4, "用途": "底部找平或移动"})

df_bom = pd.DataFrame(bom_items)

# --- 主界面展示 ---
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader(f"📐 3D 结构预览 ({furniture_type})")
    fig = draw_3d_frame(L, W, H, tiers, furniture_type)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("⚖️ 工程与组装评估")
    max_load = PROFILES[profile_choice]["max_load_kg"]
    st.info(f"**选定型材:** {profile_choice} ({profile_w}mm x {profile_w}mm)\n\n"
            f"**预估单层承重参考:** 约 {max_load} kg\n\n"
            f"**面板建议:** {PANELS[panel_choice]['desc']}")
    
    if furniture_type == "多层置物架":
        st.write("💡 **组装提示：**")
        st.write(f"- 这是一个 {tiers} 层的架子。建议先在地上将左右两侧的“日”字形框架组装好，然后再立起来连接长横梁。")
        st.write(f"- 共需要拧 **{bracket_qty * 2}** 颗螺丝，建议准备一个电动螺丝刀。")
        if H > 1800 and W < 400:
             st.warning("⚠️ **防倾倒警告：** 高度太高且进深太窄，重心不稳，建议使用膨胀螺丝将顶部固定在墙上（L型防倒件）！")

st.divider()

st.subheader("🛒 采购材料清单 (BOM)")
st.write("💡 **购买指南：** 将清单发给铝型材卖家，型材尺寸按表格给的**精确毫米数**免费切割。五金件最好多买 10% 备用，以防组装时滑丝或丢失。")
st.dataframe(df_bom, use_container_width=True, hide_index=True)

# 导出 CSV 按钮
csv = df_bom.to_csv(index=False).encode('utf-8-sig')
st.download_button(
    label="📥 下载 BOM 清单 (CSV格式)",
    data=csv,
    file_name='DIY_Shelves_BOM.csv',
    mime='text/csv',
)
