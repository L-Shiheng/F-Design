import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ==========================================
# 市场参考价格库 (包含安全防护配件)
# ==========================================
PRICES = {
    "profile_4040": 45.0,  
    "profile_3030": 25.0,  
    "panel_solid": 200.0,  
    "bracket_std": 2.5,    # 标准外露角码 + 螺丝
    "bracket_cover": 0.8,  # 角码圆润盖板
    "bracket_hidden": 4.5, # 隐形内置连接件 (更贵但绝对安全平整)
    "slot_strip": 3.0,     # PVC平槽胶条 (3元/米)
    "end_cap": 0.5         # 圆润塑料端盖
}

def create_box_traces(x, y, z, dx, dy, dz, color, name):
    xx = [x, x+dx, x+dx, x, x, x+dx, x+dx, x]
    yy = [y, y, y+dy, y+dy, y, y, y+dy, y+dy]
    zz = [z, z, z, z, z+dz, z+dz, z+dz, z+dz]
    i = [0, 0, 4, 4, 0, 0, 3, 3, 0, 0, 1, 1]
    j = [1, 2, 5, 6, 1, 5, 2, 6, 3, 7, 2, 6]
    k = [2, 3, 6, 7, 5, 4, 6, 7, 7, 4, 6, 5]
    mesh = go.Mesh3d(x=xx, y=yy, z=zz, i=i, j=j, k=k, color=color, opacity=0.9, name=name, showlegend=False, flatshading=True)
    x_edges = [x, x+dx, x+dx, x, x, x, x+dx, x+dx, x+dx, x+dx, x, x, x, x, x+dx, x+dx]
    y_edges = [y, y, y+dy, y+dy, y, y, y, y, y+dy, y+dy, y+dy, y+dy, y+dy, y, y, y+dy]
    z_edges = [z, z, z, z, z, z+dz, z+dz, z, z, z+dz, z+dz, z, z+dz, z+dz, z+dz, z+dz]
    edges = go.Scatter3d(x=x_edges, y=y_edges, z=z_edges, mode='lines', line=dict(color='#2c3e50', width=3), showlegend=False, hoverinfo='skip')
    return [mesh, edges]

st.set_page_config(page_title="Pro 铝型材装配设计", layout="wide")
st.title("🏗️ 工业级半高床设计器 (注重人员安全版)")

with st.sidebar:
    st.header("📐 空间参数")
    L = st.number_input("床总长度 (mm)", value=2000, step=10)
    W = st.number_input("床总宽度 (mm)", value=1200, step=10)
    H_bed = st.number_input("床架净空高度 (mm)", value=1300, step=10)
    H_rail = st.number_input("护栏高度 (mm)", value=400, step=10)
    
    st.header("🚪 入口与爬梯")
    entrance_pos = st.radio("上下床入口位置", ["左侧", "右侧"])
    ladder_W = st.number_input("爬梯宽度 (mm)", min_value=300, max_value=800, value=450, step=10)
    
    st.header("⚙️ 材料与安全配置")
    profile_type = st.selectbox("主型材型号", ["4040", "3030"])
    pw = int(profile_type) // 100 
    
    # 新增安全防护选项
    safety_level = st.radio(
        "人员安全防护等级", 
        ["工业基础 (无防护，有磕碰风险)", 
         "家用标准 (加装角码盖板 + 端盖)", 
         "母婴级防磕碰 (内置隐形连接件 + 全包覆平槽胶条)"],
        index=2
    )

fig = go.Figure()
bom_raw = []
total_profile_length_mm = 0 # 用于计算需要多少米防撞胶条

def add_part(module, name, x, y, z, dx, dy, dz, color):
    global total_profile_length_mm
    traces = create_box_traces(x, y, z, dx, dy, dz, color, name)
    fig.add_traces(traces)
    length_mm = int(max(dx, dy, dz))
    total_profile_length_mm += length_mm
    
    unit_cost = (length_mm / 1000.0) * PRICES[f"profile_{profile_type}"]
    bom_raw.append({"模块": module, "物料名称": f"{profile_type} 型材", "规格/尺寸": f"{length_mm} mm", "单价预估(元)": round(unit_cost, 2)})

# 颜色
C_PILLAR, C_BEAM, C_RAIL, C_LADDER, C_PANEL = '#7f8c8d', '#bdc3c7', '#f1c40f', '#3498db', '#d35400'
H_total = H_bed + H_rail

# 1. 立柱
for px, py in [(0, 0), (L-pw, 0), (0, W-pw), (L-pw, W-pw), (L/2-pw/2, 0), (L/2-pw/2, W-pw)]:
    add_part("主框架", "立柱", px, py, 0, pw, pw, H_total, C_PILLAR)

# 2. 横梁
beam_L_half, beam_W_full = L/2 - 1.5*pw, W - 2*pw
for z_level, m_name in [(0, "底部地梁"), (H_bed-pw, "床板承重架")]:
    add_part(m_name, "长横梁", pw, 0, z_level, beam_L_half, pw, pw, C_BEAM)
    add_part(m_name, "长横梁", L/2+pw/2, 0, z_level, beam_L_half, pw, pw, C_BEAM)
    add_part(m_name, "长横梁", pw, W-pw, z_level, beam_L_half, pw, pw, C_BEAM)
    add_part(m_name, "长横梁", L/2+pw/2, W-pw, z_level, beam_L_half, pw, pw, C_BEAM)
    add_part(m_name, "宽横梁", 0, pw, z_level, pw, beam_W_full, pw, C_BEAM)
    add_part(m_name, "宽横梁", L-pw, pw, z_level, pw, beam_W_full, pw, C_BEAM)
    add_part(m_name, "宽横撑", L/2-pw/2, pw, z_level, pw, beam_W_full, pw, C_BEAM)

# 3. 护栏
z_rail = H_total - pw
add_part("安全护栏", "后护栏", pw, W-pw, z_rail, L-2*pw, pw, pw, C_RAIL)
add_part("安全护栏", "左护栏", 0, pw, z_rail, pw, beam_W_full, pw, C_RAIL)
add_part("安全护栏", "右护栏", L-pw, pw, z_rail, pw, beam_W_full, pw, C_RAIL)
if entrance_pos == "左侧":
    add_part("安全护栏", "前护栏", pw + ladder_W, 0, z_rail, (L - pw) - (pw + ladder_W), pw, pw, C_RAIL)
else:
    add_part("安全护栏", "前护栏", pw, 0, z_rail, (L - pw - ladder_W) - pw, pw, pw, C_RAIL)

# 4. 爬梯
ladder_x = pw if entrance_pos == "左侧" else (L - pw - ladder_W)
add_part("爬梯模块", "爬梯立杆", ladder_x, -pw, 0, pw, pw, H_total, C_LADDER)
add_part("爬梯模块", "爬梯立杆", ladder_x + ladder_W - pw, -pw, 0, pw, pw, H_total, C_LADDER)
for s in range(1, int(H_bed // 280) + 1):
    add_part("爬梯模块", "踏步", ladder_x + pw, -pw, s * 280, ladder_W - 2*pw, pw, pw, C_LADDER)

# 5. 面板
inner_L, inner_W = L - 2*pw - 2, W - 2*pw - 2
fig.add_traces(create_box_traces(pw+1, pw+1, H_bed-10, inner_L, inner_W, 10, C_PANEL, "实木床板"))
bom_raw.append({"模块": "木作模块", "物料名称": "18mm实木床板", "规格/尺寸": f"{inner_L} × {inner_W} mm", "单价预估(元)": round((inner_L/1000)*(inner_W/1000)*PRICES["panel_solid"], 2)})

fig.update_layout(scene=dict(aspectmode='data'), margin=dict(l=0, r=0, b=0, t=0), height=500)

# ==========================================
# 财务聚合与安全防护配件推算
# ==========================================
df_raw = pd.DataFrame(bom_raw)
df_grouped = df_raw.groupby(['模块', '物料名称', '规格/尺寸', '单价预估(元)']).size().reset_index(name='数量')
df_grouped['小计(元)'] = df_grouped['单价预估(元)'] * df_grouped['数量']

hardware_bom = []
profile_count = len(df_raw) - 1 
bracket_qty = profile_count * 2

# 根据安全等级计算五金配件
if safety_level == "工业基础 (无防护，有磕碰风险)":
    cost = bracket_qty * PRICES["bracket_std"]
    hardware_bom.append({"模块": "五金及安全配件", "物料名称": "标准直角角码+螺丝", "规格/尺寸": "外露型", "单价预估(元)": PRICES["bracket_std"], "数量": bracket_qty, "小计(元)": cost})
    
elif safety_level == "家用标准 (加装角码盖板 + 端盖)":
    cost1 = bracket_qty * PRICES["bracket_std"]
    cost2 = bracket_qty * PRICES["bracket_cover"]
    cap_qty = 14 # 估算立柱顶部和爬梯端头
    cost3 = cap_qty * PRICES["end_cap"]
    hardware_bom.append({"模块": "五金及安全配件", "物料名称": "标准直角角码+螺丝", "规格/尺寸": "外露型", "单价预估(元)": PRICES["bracket_std"], "数量": bracket_qty, "小计(元)": cost1})
    hardware_bom.append({"模块": "五金及安全配件", "物料名称": "护角防撞盖板", "规格/尺寸": "配套角码", "单价预估(元)": PRICES["bracket_cover"], "数量": bracket_qty, "小计(元)": cost2})
    hardware_bom.append({"模块": "五金及安全配件", "物料名称": "圆润塑料端盖", "规格/尺寸": "封堵型材端面", "单价预估(元)": PRICES["end_cap"], "数量": cap_qty, "小计(元)": cost3})

elif safety_level == "母婴级防磕碰 (内置隐形连接件 + 全包覆平槽胶条)":
    cost1 = bracket_qty * PRICES["bracket_hidden"]
    strip_meters = int(total_profile_length_mm * 2 / 1000) # 假设一根型材平均2个面需要封槽
    cost2 = strip_meters * PRICES["slot_strip"]
    cap_qty = 14
    cost3 = cap_qty * PRICES["end_cap"]
    hardware_bom.append({"模块": "五金及安全配件", "物料名称": "隐形内置连接件", "规格/尺寸": "需型材打孔", "单价预估(元)": PRICES["bracket_hidden"], "数量": bracket_qty, "小计(元)": cost1})
    hardware_bom.append({"模块": "五金及安全配件", "物料名称": "PVC防撞平槽胶条", "规格/尺寸": "填平凹槽防割伤", "单价预估(元)": PRICES["slot_strip"], "数量": strip_meters, "小计(元)": cost2})
    hardware_bom.append({"模块": "五金及安全配件", "物料名称": "圆润塑料端盖", "规格/尺寸": "封堵型材端面", "单价预估(元)": PRICES["end_cap"], "数量": cap_qty, "小计(元)": cost3})

df_hardware = pd.DataFrame(hardware_bom)
df_final = pd.concat([df_grouped, df_hardware], ignore_index=True)
total_cost = df_final['小计(元)'].sum()

# ==========================================
# 界面渲染输出
# ==========================================
col1, col2 = st.columns([5, 3])

with col1:
    st.plotly_chart(fig, use_container_width=True)
    if "母婴级" in safety_level:
        st.success("✅ 当前为最高安全标准。框架表面将没有突出的螺丝和角码，所有凹槽都会被柔软的胶条填平，立柱顶端也会被封堵。")
    elif "工业基础" in safety_level:
        st.error("⚠️ 警告：不建议将工业基础标准直接用于儿童床或频繁接触的家具，存在边缘割伤风险。")

with col2:
    st.metric(label="💰 预估总造价", value=f"¥ {total_cost:,.2f}")
    st.dataframe(df_final[['模块', '物料名称', '规格/尺寸', '数量', '小计(元)']].sort_values(by=['模块', '小计(元)'], ascending=[True, False]), use_container_width=True, hide_index=True)
