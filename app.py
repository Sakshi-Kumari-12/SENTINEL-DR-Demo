import streamlit as st
import pandas as pd
import numpy as np
import time
import random
from datetime import datetime, timedelta
import json
import plotly.graph_objects as go
import plotly.express as px


import streamlit as st
import pandas as pd
import numpy as np
import time
import random
from datetime import datetime, timedelta
import json
import plotly.graph_objects as go
import plotly.express as px

# ===================== FORCE SIDEBAR TO ALWAYS BE VISIBLE =====================
st.markdown("""
<style>
    /* Force sidebar to always be visible and expanded */
    section[data-testid="stSidebar"] {
        min-width: 300px !important;
        max-width: 300px !important;
        transform: translateX(0px) !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    
    /* Show the sidebar toggle button */
    button[title="View fullscreen"] {
        display: block !important;
    }
    
    /* Hide the collapse button if it exists */
    button[data-testid="baseButton-headerNoPadding"] {
        display: none !important;
    }
    
    /* Make sure main content doesn't overlap */
    section[data-testid="stMainBlockContainer"] {
        margin-left: 300px !important;
    }
</style>
""", unsafe_allow_html=True)

# Force expanded sidebar in page config
st.set_page_config(
    page_title="SENTINEL-DR | Disaster Response",
    page_icon="🚁",
    layout="wide",
    initial_sidebar_state="expanded"  # THIS IS CRITICAL!
)


# Force sidebar to always be visible
st.markdown("""
<style>
    [data-testid="stSidebar"][aria-expanded="true"]{
        min-width: 300px;
        max-width: 300px;
    }
</style>
""", unsafe_allow_html=True)

# ===================== CONFIGURATION =====================
st.set_page_config(
    page_title="SENTINEL-DR | Disaster Response",
    page_icon="🚁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================== CUSTOM CSS =====================
st.markdown("""
<style>
    /* Main container */
    .main-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Cards */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        border-left: 5px solid #3B82F6;
        transition: transform 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
    }
    
    /* Alerts */
    .alert-critical {
        background: linear-gradient(90deg, #FEE2E2 0%, #FECACA 100%);
        border-left: 5px solid #DC2626;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        animation: pulse 2s infinite;
    }
    
    .alert-high {
        background: linear-gradient(90deg, #FEF3C7 0%, #FDE68A 100%);
        border-left: 5px solid #F59E0B;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    .alert-medium {
        background: linear-gradient(90deg, #DBEAFE 0%, #BFDBFE 100%);
        border-left: 5px solid #3B82F6;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.8; }
        100% { opacity: 1; }
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        background-color: #F3F4F6;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ===================== INITIALIZE SESSION STATE =====================
if 'mission_active' not in st.session_state:
    st.session_state.mission_active = False
if 'alerts' not in st.session_state:
    st.session_state.alerts = []
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'drone_data' not in st.session_state:
    st.session_state.drone_data = []
if 'detection_history' not in st.session_state:
    st.session_state.detection_history = []

# ===================== UTILITY FUNCTIONS =====================
def generate_map_data(center_lat=18.52, center_lon=73.85, points=20):
    """Generate realistic disaster zone data"""
    data = []
    types = ['survivor', 'hazard', 'safe', 'damage', 'medical']
    weights = [0.3, 0.25, 0.2, 0.15, 0.1]  # Probability weights
    
    for _ in range(points):
        lat = center_lat + random.uniform(-0.015, 0.015)
        lon = center_lon + random.uniform(-0.015, 0.015)
        point_type = random.choices(types, weights=weights)[0]
        
        # Add some clustering
        if random.random() > 0.7 and data:
            last_point = data[-1]
            lat = last_point['lat'] + random.uniform(-0.002, 0.002)
            lon = last_point['lon'] + random.uniform(-0.002, 0.002)
        
        data.append({
            'lat': lat,
            'lon': lon,
            'type': point_type,
            'confidence': random.randint(75, 98),
            'size': random.randint(20, 60),
            'id': f"{point_type[:3].upper()}_{len(data)+1}"
        })
    
    return pd.DataFrame(data)

def generate_alert():
    """Generate a realistic alert"""
    alert_types = [
        ("👤 Survivor Detected", "critical", "Person trapped under debris", 92),
        ("🔥 Fire Hazard", "critical", "Electrical fire spreading rapidly", 88),
        ("🏚️ Structural Collapse", "high", "Building partially collapsed", 85),
        ("🚧 Route Blocked", "high", "Main access road blocked", 90),
        ("💧 Flooding Detected", "medium", "Water level rising in Zone C", 82),
        ("🏥 Medical Emergency", "high", "Injured person requires attention", 87),
        ("⚡ Power Outage", "medium", "Grid failure in affected area", 79),
        ("📡 Communication Gap", "low", "Weak signal in Zone B", 75),
    ]
    
    alert_type, priority, description, base_conf = random.choice(alert_types)
    zone = f"Zone {chr(65 + random.randint(0, 4))}-{random.randint(1, 20):02d}"
    time_offset = random.randint(1, 30)
    alert_time = (datetime.now() - timedelta(minutes=time_offset)).strftime("%H:%M:%S")
    
    return {
        'type': alert_type,
        'priority': priority,
        'description': description,
        'zone': zone,
        'time': alert_time,
        'confidence': random.randint(base_conf - 5, base_conf + 3),
        'id': f"ALT_{len(st.session_state.alerts)+1:04d}"
    }

def create_drone_status():
    """Create drone status data"""
    drones = []
    statuses = ['Active', 'Active', 'Returning', 'Maintenance']
    zones = ['Zone A', 'Zone B', 'Zone C', 'Base']
    
    for i in range(4):
        drones.append({
            'name': f'DRONE-{i+1}',
            'status': statuses[i],
            'battery': random.randint(40, 95),
            'location': zones[i],
            'altitude': f'{random.randint(50, 200)}m',
            'speed': f'{random.randint(15, 45)} km/h',
            'temp': f'{random.randint(20, 45)}°C',
            'signal': random.choice(['Excellent', 'Good', 'Fair', 'Poor']),
            'last_update': (datetime.now() - timedelta(seconds=random.randint(10, 300))).strftime("%H:%M:%S")
        })
    
    return drones

# ===================== HEADER =====================
st.markdown("""
<div class="main-header">
    <h1 style="margin:0; font-size:2.8rem;">🚁 SENTINEL-DR</h1>
    <h3 style="margin:0; font-weight:300;">AI-Powered Disaster Response Command Center</h3>
    <p style="margin-top:0.5rem; opacity:0.9;">Team G | DIAT Pune Technical Hackathon 2025 | Real-time Simulation</p>
</div>
""", unsafe_allow_html=True)

# ===================== SIDEBAR =====================
with st.sidebar:
    st.image("https://img.icons8.com/color/144/000000/drone.png", width=100)
    st.title("Command Center")
    
    # System Status
    st.markdown("### ⚙️ System Status")
    
    status_cols = st.columns(2)
    with status_cols[0]:
        st.metric("AI System", "Online", delta="92% acc")
    with status_cols[1]:
        st.metric("Comms", "Strong", delta="-2ms")
    
    # Health indicators
    st.progress(0.92, text="System Health: 92%")
    st.progress(0.85, text="Network: 85%")
    st.progress(0.78, text="Battery Avg: 78%")
    
    st.markdown("---")
    
    # Quick Actions
    st.markdown("### ⚡ Quick Actions")
    
    if st.button("🔄 Refresh All Data", type="secondary", use_container_width=True):
        st.session_state.drone_data = create_drone_status()
        st.rerun()
    
    if st.button("📡 Test Communication", type="secondary", use_container_width=True):
        with st.spinner("Testing comms..."):
            time.sleep(1)
            st.success("All drones responding!")
    
    if st.button("🆘 Emergency SOS", type="primary", use_container_width=True):
        st.error("""
        🚨 SOS SENT TO:
        • NDRF Control Room
        • Local Emergency Services
        • District Disaster Management
        • Medical Response Teams
        """)
    
    st.markdown("---")
    
    # Team Info
    st.markdown("### 👥 Team G")
    st.info("""
    **Harshal Diwate** - System Architect  
    **Shashank Shekhar** - AI/ML Engineer  
    **Sakshi Kumari** - Frontend Developer  
    **Urvashi Boda** - Backend Engineer
    """)

# ===================== MAIN DASHBOARD - TABS =====================
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Mission Control", "📡 Live Operations", "🚨 Intelligence", "📊 Analytics"])

# ===================== TAB 1: MISSION CONTROL =====================
with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🌍 Real-Time Disaster Zone Map")
        
        # Generate dynamic map data
        map_df = generate_map_data()
        
        # Color mapping
        color_map = {
            'survivor': '#00FF00',  # Green
            'hazard': '#FF0000',    # Red
            'safe': '#0000FF',      # Blue
            'damage': '#FFA500',    # Orange
            'medical': '#800080'    # Purple
        }
        
        map_df['color'] = map_df['type'].map(color_map)
        
        # Display map
        st.map(map_df, size='size', color='color')
        
        # Map controls
        map_col1, map_col2, map_col3 = st.columns(3)
        with map_col1:
            if st.button("🔄 Update Map", key="update_map"):
                st.rerun()
        with map_col2:
            st.download_button(
                "📥 Export Map Data",
                data=map_df.to_csv(),
                file_name="disaster_zone_data.csv",
                mime="text/csv"
            )
        with map_col3:
            st.caption(f"🔄 Last updated: {datetime.now().strftime('%H:%M:%S')}")
        
        # Map legend
        st.markdown("""
        **Legend:** 
        <span style='color:#00FF00; font-weight:bold'>🟢 Survivors</span> | 
        <span style='color:#FF0000; font-weight:bold'>🔴 Hazards</span> | 
        <span style='color:#0000FF; font-weight:bold'>🔵 Safe Zones</span> | 
        <span style='color:#FFA500; font-weight:bold'>🟠 Structural Damage</span> | 
        <span style='color:#800080; font-weight:bold'>🟣 Medical Needs</span>
        """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("🚀 Mission Configuration")
        
        with st.form("mission_form", border=False):
            # Disaster selection
            disaster = st.selectbox(
                "Disaster Type",
                ["Earthquake", "Flood", "Hurricane/Cyclone", "Wildfire", 
                 "Building Collapse", "Industrial Accident", "Tsunami"],
                index=0
            )
            
            # Severity
            severity = st.slider("Severity Level", 1, 10, 7)
            
            # Drone configuration
            drone_count = st.radio(
                "Drone Fleet",
                [1, 2, 3, 4],
                horizontal=True,
                captions=["Solo", "Duo", "Trio", "Full Squad"]
            )
            
            # Mission parameters
            col_a, col_b = st.columns(2)
            with col_a:
                radius = st.number_input("Radius (km)", 1.0, 10.0, 3.0)
            with col_b:
                altitude = st.selectbox("Altitude", ["50m", "100m", "150m", "200m"])
            
            # Launch button
            submitted = st.form_submit_button(
                "🚀 LAUNCH MISSION", 
                type="primary", 
                use_container_width=True
            )
            
            if submitted:
                st.session_state.mission_active = True
                st.session_state.start_time = datetime.now()
                st.session_state.disaster_type = disaster
                st.session_state.drone_data = create_drone_status()
                
                # Show launch animation
                launch_placeholder = st.empty()
                with launch_placeholder.container():
                    st.balloons()
                    st.success(f"""
                    ✅ **MISSION LAUNCHED SUCCESSFULLY!**
                    
                    **Details:**
                    • Type: {disaster}
                    • Severity: {severity}/10
                    • Drones: {drone_count}
                    • Radius: {radius} km
                    • Start: {st.session_state.start_time.strftime('%H:%M:%S')}
                    
                    **Status:** Drones deploying to disaster zone...
                    """)
                
                time.sleep(2)
                launch_placeholder.empty()
                st.rerun()
        
        # Live Metrics
        st.subheader("📊 Live Mission Metrics")
        
        metrics = [
            ("Area Covered", f"{random.uniform(1.2, 2.8):.1f} km²", f"+{random.uniform(0.1, 0.5):.1f}"),
            ("Flight Time", f"{random.randint(15, 40)} min", f"+{random.randint(1, 5)}"),
            ("Data Collected", f"{random.randint(300, 1200)} MB", f"+{random.randint(50, 200)}"),
            ("Power Usage", f"{random.randint(20, 45)}%", f"-{random.randint(1, 5)}"),
        ]
        
        for title, value, delta in metrics:
            col_m1, col_m2 = st.columns([3, 1])
            with col_m1:
                st.metric(title, value, delta)
        
        # Mission Timer
        if st.session_state.mission_active and st.session_state.start_time:
            elapsed = datetime.now() - st.session_state.start_time
            elapsed_min = int(elapsed.total_seconds() / 60)
            st.info(f"⏱️ **Mission Duration:** {elapsed_min} minutes")

# ===================== TAB 2: LIVE OPERATIONS =====================
with tab2:
    st.subheader("📡 Drone Fleet Monitoring")
    
    # Drone Status Grid
    if not st.session_state.drone_data:
        st.session_state.drone_data = create_drone_status()
    
    drone_cols = st.columns(4)
    
    for idx, col in enumerate(drone_cols):
        with col:
            drone = st.session_state.drone_data[idx]
            
            # Drone card
            st.markdown(f'<div class="metric-card">', unsafe_allow_html=True)
            
            # Status indicator
            if drone['status'] == 'Active':
                status_color = "🟢"
                status_style = "color: #10B981;"
            elif drone['status'] == 'Returning':
                status_color = "🟡"
                status_style = "color: #F59E0B;"
            else:
                status_color = "🔴"
                status_style = "color: #DC2626;"
            
            st.markdown(f"### {status_color} {drone['name']}")
            st.markdown(f"<p style='{status_style}'><b>Status:</b> {drone['status']}</p>", unsafe_allow_html=True)
            
            # Metrics
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.metric("Battery", f"{drone['battery']}%")
            with col_d2:
                st.metric("Signal", drone['signal'])
            
            # Details
            st.markdown(f"""
            **Location:** {drone['location']}
            **Altitude:** {drone['altitude']}
            **Speed:** {drone['speed']}
            **Temp:** {drone['temp']}
            **Updated:** {drone['last_update']}
            """)
            
            # Battery visual
            battery_color = "green" if drone['battery'] > 70 else "orange" if drone['battery'] > 40 else "red"
            st.progress(drone['battery']/100, text="Battery Level")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # AI Processing Dashboard
    st.subheader("🤖 AI Processing Center")
    
    ai_cols = st.columns(4)
    
    ai_metrics = [
        ("Frames Processed", f"{random.randint(2500, 5000):,}", f"{random.randint(30, 60)} fps"),
        ("Detection Accuracy", f"{random.uniform(88.5, 96.5):.1f}%", f"+{random.uniform(0.5, 2.5):.1f}%"),
        ("Processing Speed", f"{random.uniform(0.5, 1.2):.2f} ms", f"-{random.uniform(0.1, 0.3):.2f} ms"),
        ("False Positives", f"{random.randint(8, 25)}", f"{random.randint(1, 5)}"),
    ]
    
    for idx, (title, value, subtitle) in enumerate(ai_metrics):
        with ai_cols[idx]:
            st.markdown(f'<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f"**{title}**")
            st.markdown(f"<h2 style='margin:0;'>{value}</h2>", unsafe_allow_html=True)
            st.markdown(f"<small>{subtitle}</small>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Detection Types Chart
    st.markdown("### 🎯 Detection Breakdown")
    
    detections = {
        "Survivors": random.randint(2, 8),
        "Structural Damage": random.randint(3, 12),
        "Fire Hazards": random.randint(0, 4),
        "Flood Areas": random.randint(0, 5),
        "Blocked Routes": random.randint(1, 6),
        "Medical Needs": random.randint(0, 3),
        "Power Outages": random.randint(0, 2),
        "Gas Leaks": random.randint(0, 1)
    }
    
    # Create bar chart
    chart_df = pd.DataFrame({
        'Category': list(detections.keys()),
        'Count': list(detections.values())
    })
    
    fig = px.bar(
        chart_df, 
        x='Category', 
        y='Count',
        color='Count',
        color_continuous_scale='Viridis',
        title="AI Detection Summary"
    )
    st.plotly_chart(fig, use_container_width=True)

# ===================== TAB 3: INTELLIGENCE =====================
with tab3:
    st.subheader("🚨 Real-Time Alert System")
    
    # Generate new alerts
    if st.button("🔄 Generate New Alerts", key="gen_alerts"):
        for _ in range(random.randint(2, 5)):
            new_alert = generate_alert()
            st.session_state.alerts.append(new_alert)
        st.rerun()
    
    # Display alerts
    if not st.session_state.alerts:
        for _ in range(5):
            st.session_state.alerts.append(generate_alert())
    
    # Sort alerts by priority
    priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    sorted_alerts = sorted(st.session_state.alerts, key=lambda x: priority_order[x['priority']])
    
    # Show last 10 alerts
    for alert in sorted_alerts[-10:]:
        if alert['priority'] == 'critical':
            st.markdown(f"""
            <div class="alert-critical">
                <h4 style="margin:0;">🚨 {alert['type']}</h4>
                <p style="margin:0.2rem 0;"><b>Location:</b> {alert['zone']}</p>
                <p style="margin:0.2rem 0;"><b>Time:</b> {alert['time']} | <b>Confidence:</b> {alert['confidence']}%</p>
                <p style="margin:0.2rem 0;"><b>Details:</b> {alert['description']}</p>
                <p style="margin:0.2rem 0;"><b>Alert ID:</b> {alert['id']}</p>
                <div style="display: flex; gap: 10px; margin-top: 10px;">
                    <button style="background: #DC2626; color: white; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer;">Dispatch Team</button>
                    <button style="background: #3B82F6; color: white; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer;">Mark Resolved</button>
                    <button style="background: #10B981; color: white; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer;">Add Notes</button>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        elif alert['priority'] == 'high':
            st.markdown(f"""
            <div class="alert-high">
                <h4 style="margin:0;">⚠️ {alert['type']}</h4>
                <p style="margin:0.2rem 0;"><b>Location:</b> {alert['zone']}</p>
                <p style="margin:0.2rem 0;"><b>Time:</b> {alert['time']} | <b>Confidence:</b> {alert['confidence']}%</p>
                <p style="margin:0.2rem 0;"><b>Details:</b> {alert['description']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        else:
            st.markdown(f"""
            <div class="alert-medium">
                <h4 style="margin:0;">ℹ️ {alert['type']}</h4>
                <p style="margin:0.2rem 0;"><b>Location:</b> {alert['zone']}</p>
                <p style="margin:0.2rem 0;"><b>Time:</b> {alert['time']} | <b>Confidence:</b> {alert['confidence']}%</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Response Recommendations
    st.subheader("🎯 Recommended Actions")
    
    recommendations = [
        {"priority": 1, "action": "Immediate evacuation of Zones A-12 to A-15", "eta": "15 min", "units": "2 Rescue Teams"},
        {"priority": 2, "action": "Fire containment at coordinates 18.525, 73.855", "eta": "20 min", "units": "1 Fire Engine"},
        {"priority": 3, "action": "Clear debris from Main Access Road", "eta": "30 min", "units": "Engineering Corps"},
        {"priority": 4, "action": "Establish field hospital at secure location", "eta": "45 min", "units": "Medical Unit"},
        {"priority": 5, "action": "Airdrop emergency supplies to marked locations", "eta": "60 min", "units": "Logistics Team"},
    ]
    
    for rec in recommendations:
        col_r1, col_r2, col_r3 = st.columns([1, 3, 2])
        with col_r1:
            st.markdown(f"**#{rec['priority']}**")
        with col_r2:
            st.write(rec['action'])
        with col_r3:
            col_eta, col_units = st.columns(2)
            with col_eta:
                st.caption(f"⏱️ {rec['eta']}")
            with col_units:
                st.caption(f"👥 {rec['units']}")

# ===================== TAB 4: ANALYTICS =====================
with tab4:
    st.subheader("📊 Mission Analytics & Reporting")
    
    # Generate Report Button
    report_col1, report_col2, report_col3 = st.columns(3)
    
    with report_col1:
        if st.button("📋 Generate Full Report", type="primary", use_container_width=True):
            with st.spinner("Compiling intelligence report..."):
                time.sleep(2)
                
                # Comprehensive report
                report = {
                    "mission_summary": {
                        "id": f"DRN-2025-{random.randint(100, 999)}-G",
                        "type": st.session_state.get('disaster_type', 'Earthquake'),
                        "start_time": st.session_state.start_time.strftime("%Y-%m-%d %H:%M:%S") if st.session_state.start_time else "N/A",
                        "duration": f"{random.randint(30, 90)} minutes",
                        "status": "Active" if st.session_state.mission_active else "Completed"
                    },
                    "operational_metrics": {
                        "area_covered": f"{random.uniform(2.5, 5.0):.1f} km²",
                        "total_flight_time": f"{random.randint(120, 300)} minutes",
                        "average_battery_used": f"{random.randint(55, 85)}%",
                        "data_transmitted": f"{random.randint(800, 2500)} MB",
                        "communication_uptime": f"{random.uniform(92.5, 99.9):.1f}%"
                    },
                    "ai_performance": {
                        "total_detections": random.randint(50, 200),
                        "accuracy_rate": f"{random.uniform(88.5, 96.5):.1f}%",
                        "processing_speed": f"{random.uniform(35, 55)} fps",
                        "false_positive_rate": f"{random.uniform(2.5, 5.5):.1f}%",
                        "average_confidence": f"{random.uniform(85.0, 94.0):.1f}%"
                    },
                    "critical_findings": [
                        f"{random.randint(2, 8)} survivors located and geo-tagged",
                        f"{random.randint(3, 10)} structural hazards identified",
                        f"{random.randint(1, 4)} active fire zones detected",
                        f"{random.randint(2, 6)} access routes partially/completely blocked",
                        f"{random.randint(3, 8)} safe zones established for evacuation",
                        f"{random.randint(1, 3)} medical emergency sites identified"
                    ],
                    "resource_assessment": {
                        "immediate_needs": {
                            "rescue_teams": random.randint(2, 5),
                            "medical_units": random.randint(1, 3),
                            "fire_engines": random.randint(1, 4),
                            "engineering_corps": random.randint(1, 3)
                        },
                        "logistics": {
                            "food_water_packs": random.randint(100, 500),
                            "medical_kits": random.randint(50, 200),
                            "temporary_shelters": random.randint(20, 100),
                            "communication_devices": random.randint(10, 50)
                        }
                    },
                    "estimated_timelines": {
                        "first_responder_arrival": f"{random.randint(8, 25)} minutes",
                        "medical_evacuation": f"{random.randint(15, 45)} minutes",
                        "hazard_containment": f"{random.randint(30, 90)} minutes",
                        "restoration_phase_1": f"{random.randint(3, 10)} hours",
                        "full_normalization": f"{random.randint(3, 10)} days"
                    },
                    "recommendations": [
                        "Priority 1: Immediate rescue operation in Zones A-12 to A-15",
                        "Priority 2: Fire containment and evacuation in high-risk zones",
                        "Priority 3: Clear primary access routes for emergency vehicles",
                        "Priority 4: Establish field hospital at coordinates 18.515, 73.845",
                        "Priority 5: Deploy temporary communication network in affected area"
                    ]
                }
                
                # Display report in expandable sections
                for section, content in report.items():
                    with st.expander(f"📄 {section.replace('_', ' ').title()}", expanded=True):
                        if isinstance(content, dict):
                            for subsection, subcontent in content.items():
                                if isinstance(subcontent, dict):
                                    st.write(f"**{subsection.replace('_', ' ').title()}:**")
                                    for key, value in subcontent.items():
                                        st.write(f"  • {key.replace('_', ' ').title()}: {value}")
                                elif isinstance(subcontent, list):
                                    st.write(f"**{subsection.replace('_', ' ').title()}:**")
                                    for item in subcontent:
                                        st.write(f"  • {item}")
                                else:
                                    st.write(f"**{subsection.replace('_', ' ').title()}:** {subcontent}")
                        elif isinstance(content, list):
                            for item in content:
                                st.write(f"• {item}")
                        else:
                            st.write(content)
                
                # Download buttons
                st.markdown("### 📥 Export Options")
                dl_col1, dl_col2, dl_col3 = st.columns(3)
                with dl_col1:
                    st.download_button(
                        label="JSON Report",
                        data=json.dumps(report, indent=2),
                        file_name=f"sentinel_dr_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                with dl_col2:
                    st.download_button(
                        label="CSV Data",
                        data="latitude,longitude,type,confidence\n18.52,73.85,command,100\n18.525,73.855,survivor,92",
                        file_name="mission_data.csv",
                        mime="text/csv"
                    )
                with dl_col3:
                    st.download_button(
                        label="PDF Summary",
                        data="PDF export would be generated in production",
                        file_name="mission_summary.txt",
                        mime="text/plain"
                    )
    
    with report_col2:
        if st.button("📈 Performance Charts", use_container_width=True):
            # Create sample performance chart
            time_data = pd.DataFrame({
                'Hour': [f'{i}:00' for i in range(24)],
                'Detection Rate': [random.randint(70, 98) for _ in range(24)],
                'Response Time': [random.randint(5, 45) for _ in range(24)],
                'Area Covered': [random.randint(1, 10) for _ in range(24)]
            })
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=time_data['Hour'], y=time_data['Detection Rate'],
                                     mode='lines+markers', name='Detection Rate',
                                     line=dict(color='#3B82F6', width=3)))
            fig.add_trace(go.Scatter(x=time_data['Hour'], y=time_data['Response Time'],
                                     mode='lines+markers', name='Response Time (min)',
                                     line=dict(color='#10B981', width=3)))
            
            fig.update_layout(
                title="Mission Performance Over Time",
                xaxis_title="Time",
                yaxis_title="Metrics",
                hovermode='x unified',
                template='plotly_white'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with report_col3:
        if st.button("🔄 Reset Simulation", type="secondary", use_container_width=True):
            st.session_state.mission_active = False
            st.session_state.alerts = []
            st.session_state.drone_data = []
            st.session_state.detection_history = []
            st.success("Simulation reset successfully!")
            time.sleep(1)
            st.rerun()
    
    # Historical Data
    st.markdown("---")
    st.subheader("📅 Mission History")
    
    missions = [
        {"date": "2025-12-10", "type": "Flood", "location": "Pune District", "duration": "2h 15m", "findings": "28 survivors, 15 hazards"},
        {"date": "2025-12-08", "type": "Earthquake", "location": "Mumbai Region", "duration": "3h 45m", "findings": "42 survivors, 32 hazards"},
        {"date": "2025-12-05", "type": "Wildfire", "location": "Western Ghats", "duration": "4h 20m", "findings": "15 survivors, 8 hazards"},
        {"date": "2025-12-02", "type": "Building Collapse", "location": "Urban Center", "duration": "1h 50m", "findings": "8 survivors, 5 hazards"},
    ]
    
    for mission in missions:
        with st.expander(f"{mission['date']}: {mission['type']} at {mission['location']}"):
            col_h1, col_h2, col_h3 = st.columns(3)
            with col_h1:
                st.metric("Duration", mission['duration'])
            with col_h2:
                st.metric("Survivors", mission['findings'].split(',')[0].split()[0])
            with col_h3:
                st.metric("Hazards", mission['findings'].split(',')[1].split()[0])

# ===================== FOOTER =====================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem; font-size: 0.9rem;">
    <p><b>🚁 SENTINEL-DR Disaster Response System</b> | Team G | DIAT Pune Technical Hackathon 2025</p>
    <p>Emergency Contacts: NDRF (108) | Disaster Management (1078) | Fire (101) | Medical (102) | Police (100)</p>
    <p style="opacity: 0.7;">⚠️ This is a simulation system for demonstration purposes. Real implementation would require drone hardware integration and emergency service coordination.</p>
    <p style="opacity: 0.7;">🔄 System updates every 30 seconds | Last update: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
</div>
""", unsafe_allow_html=True)

# Auto-refresh simulation
if st.session_state.mission_active:
    time.sleep(0.5)
    # Auto-generate occasional new alerts
    if random.random() > 0.7:  # 30% chance
        st.session_state.alerts.append(generate_alert())