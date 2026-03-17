import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 数据库预设 ---
PROFILES = {
    "2020型": {"width": 20, "max_load_kg": 50},
    "3030型": {"width": 30, "max_load_kg": 150},
    "4040型": {"width": 40, "max_load_kg": 300},
}

PANELS = {
    "实木拼板 (18mm)": {"desc": "美观，适合做桌面或高端书架"},
    "亚克力板 (5mm)": {"desc": "透明，适合做防尘罩、轻型展示架"},
    "密度板/免漆板 (15mm)": {"desc": "性价比高，最适合做多层储物架"},
}

def draw_3d_frame(L, W, H, tiers, furniture_type):
    """绘制简单的 3D 框架"""
    fig = go.Figure()
    # 4根立柱
    columns = [
        ([0, 0], [0, 0], [0, H]), ([L, L], [0, 0], [0, H]),
        ([L, L], [W, W], [0, H]), ([0, 0], [W, W], [0, H])
    ]
    for x, y, z in columns:
        fig.add_trace(go.Scatter3d(x=x, y=y, z=z, mode='lines', line=dict(color='#7f8c8d', width=6), showlegend=False))
    
    # 层高计算
    if furniture_type == "多层置物架" and tiers > 1:
        z_levels = [H * i / (tiers - 1) for i in range(tiers)]
    elif furniture_type == "简易四方箱体":
        z_levels = [0, H]
    else:
        z_levels = [H]

    for z in z_levels:
        x_rect = [0, L, L, 0, 0]
        y_rect = [0, 0, W, W, 0]
        z_rect = [z, z, z, z, z]
        fig.add_trace(go.Scatter3d(x=x_rect, y=y_rect, z=z_rect, mode='lines', line=dict(color='#3498db', width=6), name=f"层高 {int(z)}mm"))
    
    fig.update_layout(scene=dict(xaxis_title='长', yaxis_title='宽', zaxis_title='高', aspectmode='data'), margin=dict(l=0, r=0, b=0, t=0), height=400, showlegend=False)
    return fig

# --- 界面布局 ---
st.set_page_config(page_title="铝型材家具设计助手", layout="wide")
st.title("🧰 DIY 铝型材家具设计助手 (精准尺寸版)")

with st.sidebar:
    st.header("1. 设定家具参数")
    furniture_type = st.selectbox("家具类型", ["多层置物架", "基础桌子/工作台", "简易四方箱体"])
    
    L = st.number_input("外部总长度 (mm)", min_value=100, max_value=3000, value=1000, step=10)
    W = st.number_input("外部总宽度 (mm)", min_value=100, max_value=2000, value=400, step=10)
    H = st.number_input("外部总高度 (mm)", min_value=100, max_value=2500, value=1500, step=10)
    
    tiers = 1
    if furniture_type == "多层置物架":
        tiers = st.number_input("层架数量 (含顶层和底层)", min_value=2, max_value=10, value=4, step=1)
    
    st.header("2. 选择材料")
    profile_choice = st.selectbox("铝型材型号", list(PROFILES.keys()), index=1)
    panel_choice = st.selectbox("面板材质", list(PANELS.keys()), index=2)

    st.header("3. 面板安装方式")
    st.info("安装方式直接影响面板的购买/切割尺寸！")
    top_panel_style = st.radio("顶层面板安装", ["平铺 (盖在型材上方)", "内嵌 (卡在立柱中间)"])
    
    lower_panel_style = "内嵌 (卡在立柱中间)"
    if tiers > 1 or furniture_type == "简易四方箱体":
        lower_panel_style = st.radio("中/下层面板安装", ["内嵌 (推荐，四边规整)", "平铺 (四角需自行锯掉缺口)"])

# --- 计算逻辑 ---
profile_w = PROFILES[profile_choice]["width"]
bom_items = []

# 1. 框架型材
bom_items.append({"部位": "主框架", "配件名称": f"立柱 - {profile_choice}", "精确切割尺寸": f"{H} mm", "数量": 4, "备注": "高度"})
l_len = L - (profile_w * 2)
w_len = W - (profile_w * 2)

if furniture_type == "多层置物架":
    qty_multiplier = tiers
elif furniture_type == "简易四方箱体":
    qty_multiplier = 2
else:
    qty_multiplier = 1

bom_items.append({"部位": "主框架", "配件名称": f"长横梁 - {profile_choice}", "精确切割尺寸": f"{l_len} mm", "数量": 2 * qty_multiplier, "备注": f"已扣除{profile_w*2}mm立柱厚度"})
bom_items.append({"部位": "主框架", "配件名称": f"宽横梁 - {profile_choice}", "精确切割尺寸": f"{w_len} mm", "数量": 2 * qty_multiplier, "备注": f"已扣除{profile_w*2}mm立柱厚度"})

# 2. 面板尺寸计算 (核心修正点)
# 预留 2mm 安装公差，防止太紧塞不进去
inner_L = L - (profile_w * 2) - 2
inner_W = W - (profile_w * 2) - 2

# 计算顶层面板
if "平铺" in top_panel_style:
    bom_items.append({"部位": "顶板", "配件名称": f"顶板 ({panel_choice})", "精确切割尺寸": f"{L} × {W} mm", "数量": 1, "备注": "直接盖在最上面"})
else:
    bom_items.append({"部位": "顶板", "配件名称": f"顶板 ({panel_choice})", "精确切割尺寸": f"{inner_L} × {inner_W} mm", "数量": 1, "备注": f"内嵌尺寸 (已扣除立柱厚度并预留2mm公差)"})

# 计算下层面板
lower_panels_qty = tiers - 1 if furniture_type == "多层置物架" else (1 if furniture_type == "简易四方箱体" else 0)
if lower_panels_qty > 0:
    if "内嵌" in lower_panel_style:
        bom_items.append({"部位": "下层板", "配件名称": f"层板 ({panel_choice})", "精确切割尺寸": f"{inner_L} × {inner_W} mm", "数量": lower_panels_qty, "备注": "内嵌尺寸 (放入框架内部)"})
    else:
        bom_items.append({"部位": "下层板", "配件名称": f"层板 ({panel_choice})", "精确切割尺寸": f"{L} × {W} mm", "数量": lower_panels_qty, "备注": f"⚠️ 警告: 四角需各切掉 {profile_w}x{profile_w}mm 的缺口才能避让立柱"})

# 3. 连接件计算
bracket_qty = 8 * qty_multiplier
bom_items.append({"部位": "五金件", "配件名称": f"{profile_choice} 直角角件", "精确切割尺寸": "标准", "数量": bracket_qty, "备注": "每层8个交角点"})
bom_items.append({"部位": "五金件", "配件名称": "内六角螺栓 + T型螺母", "精确切割尺寸": "配套尺寸", "数量": bracket_qty * 2, "备注": "固定角件必备"})

df_bom = pd.DataFrame(bom_items)

# --- 主界面展示 ---
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("📐 3D 结构预览")
    fig = draw_3d_frame(L, W, H, tiers, furniture_type)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("💡 面板安装图解说明")
    if "内嵌" in top_panel_style or ("内嵌" in lower_panel_style and lower_panels_qty > 0):
        st.success(f"**内嵌尺寸计算逻辑：**\n\n以长边为例：总长 {L}mm - 左侧立柱 {profile_w}mm - 右侧立柱 {profile_w}mm - 安装余量(公差) 2mm = **{inner_L}mm**。宽边同理。这样板子正好能平滑地放入型材组成的方框中。")
    if "平铺" in lower_panel_style and lower_panels_qty > 0:
        st.warning(f"**⚠️ 避让切角警告：**\n\n您选择了中/下层板采用【平铺】。因为四角有贯穿的立柱挡着，您买回板子后，必须自己用工具在板子的四个角各切掉一个 **{profile_w} × {profile_w} mm** 的正方形缺口，否则板子无法放平！")

st.divider()

st.subheader("🛒 精准采购材料清单 (BOM)")
st.write("现在的清单已经考虑了面板安装方式及立柱厚度的扣减，可以直接发给商家进行裁切了。")
st.dataframe(df_bom, use_container_width=True, hide_index=True)

csv = df_bom.to_csv(index=False).encode('utf-8-sig')
st.download_button(label="📥 下载精准 BOM 清单 (CSV格式)", data=csv, file_name='DIY_Furniture_Accurate_BOM.csv', mime='text/csv')
