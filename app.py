import streamlit as st
from google import genai
import PIL.Image
import streamlit.components.v1 as components

API_KEYS = st.secrets["gemini_api_keys"]

if "current_key_index" not in st.session_state:
    st.session_state.current_key_index = 0

if "checker_history" not in st.session_state:
    st.session_state.checker_history = []

def get_gemini_client():
    idx = st.session_state.current_key_index
    active_key = API_KEYS[idx % len(API_KEYS)]
    return genai.Client(api_key=active_key)

st.markdown("""
<style>
    .gemini-loader {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-family: 'Source Sans Pro', sans-serif;
        font-weight: bold;
        font-size: 18px;
        margin-bottom: 20px;
        color: inherit;
    }
    .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: currentColor;
        animation: pulse 1.4s infinite ease-in-out both;
    }
    .dot:nth-child(2) { animation-delay: 0.2s; }
    .dot:nth-child(3) { animation-delay: 0.4s; }

    @keyframes pulse {
        0%, 80%, 100% { transform: scale(0); opacity: 0.3; }
        40% { transform: scale(1.0); opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

st.title("MathemaCheck AI 🚀")
st.write("Upload a photo of handwritten math steps to check for errors instantly.")
st.divider()

uploaded_files = st.file_uploader("Choose math problem images...", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    master_analyze = st.button("🚀 Analyze All Worksheets", type="primary", use_container_width=True)
    st.write("---")
    
    tab_titles = [f"📄 {file.name}" for file in uploaded_files]
    tabs = st.tabs(tab_titles)
    
    for i, uploaded_file in enumerate(uploaded_files):
        with tabs[i]:
            image = PIL.Image.open(uploaded_file)
            
            col1, col2 = st.columns([1, 1.2], gap="large")
            
            with col1:
                st.subheader("📸 Student Worksheet")
                st.image(image, caption=uploaded_file.name, use_container_width=True)
                
            with col2:
                st.subheader("📋 AI's Feedback Workspace")
                
                cached_feedback = next((item["feedback"] for item in st.session_state.checker_history if item["filename"] == uploaded_file.name), None)
                
                if master_analyze and not cached_feedback:
                    loader_placeholder = st.empty()
                    loader_placeholder.markdown("""
                        <div class='gemini-loader'>
                            <span>Analyzing steps</span>
                            <div class='dot'></div>
                            <div class='dot'></div>
                            <div class='dot'></div>
                        </div>
                    """, unsafe_allow_html=True)

                    teacher_prompt = """
                    You are an automated math grading script. Do not write a paragraph response. Do not use filler sentences like 'The problem involves...'. 

                    Output ONLY these 6 structural points exactly:
                    ### 📋 AI's Feedback
                    1. **Board/Topic:** State ONLY the math topic and detected board (O-Level or Pakistan Board or Other Board).
                    2. **Error Check:** Point out the exact line an error occurred, or state 'No errors detected' if flawless.
                    3. **Correct Working:** Provide only the core step-by-step mathematical math lines and final correct answer.
                    
                    ### 🎯 Examiner Grading & Marks Breakdown
                    4. **Criteria used:** State the exact mark allocation type based on the board.
                    5. **Marks Breakdown:** List only the marks won/lost.
                    6. **Score:** End immediately on a new line with exactly: '**Total Marks Awarded: X / Y**'.
                    """

                    max_attempts = len(API_KEYS)
                    attempt = 0
                    success = False

                    while attempt < max_attempts and not success:
                        try:
                            current_client = get_gemini_client()
                            
                            response = current_client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=[image, teacher_prompt]
                            )
                            
                            loader_placeholder.empty()
                            st.success("Analysis Complete!")
                            
                            st.session_state.checker_history.append({
                                "filename": uploaded_file.name,
                                "feedback": response.text
                            })
                            
                            success = True
                            
                        except Exception as e:
                            err_msg = str(e).upper()
                            
                            if "RESOURCE_EXHAUSTED" in err_msg or "QUOTA" in err_msg:
                                st.session_state.current_key_index += 1
                                attempt += 1
                                if attempt < max_attempts:
                                    st.warning(f"🔄 Switching to a different ai model...")
                                continue
                                
                            else:
                                loader_placeholder.empty()
                                if "503" in err_msg or "UNAVAILABLE" in err_msg:
                                    st.warning("⚠️ AI server is busy. Click 'Analyze All Worksheets' again in 10-15 seconds!")
                                else:
                                    st.error(f"Something went wrong: {e}")
                                break

                    if not success and attempt >= max_attempts:
                        loader_placeholder.empty()
                        st.error("🚫 **All AI's have been exhausted please return after a couple hours!**")
                            
                elif cached_feedback:
                    st.success("Analysis Loaded from Cache!")
                else:
                    st.info("Click the 'Analyze All Worksheets' button above to generate feedback.")

            current_feedback = next((item["feedback"] for item in st.session_state.checker_history if item["filename"] == uploaded_file.name), None)
            
            if current_feedback:
                st.write("---")
                st.markdown(current_feedback)

st.divider()
st.subheader("💬 Send Feedback")
st.write("Have a suggestion or found a bug? Let me know!")

feedback_name = st.text_input("Your Name (optional)")
feedback_msg = st.text_area("Your Feedback", placeholder="Write your feedback here...")
send_feedback = st.button("📨 Send Feedback")

if send_feedback:
    if feedback_msg.strip() == "":
        st.warning("Please write something before sending!")
    else:
        safe_name = (feedback_name if feedback_name else "Anonymous").replace('"', '')
        safe_msg = feedback_msg.replace("`", "'").replace("\\", "")
        components.html(f"""
        <script src="https://cdn.jsdelivr.net/npm/@emailjs/browser@4/dist/email.min.js"></script>
        <script>
        window.onload = function() {{
            emailjs.init("Hk7AeN-dFBPbZAafn");
            emailjs.send("service_h3fhqlx", "template_0mvgkqn", {{
                from_name: "{safe_name}",
                message: `{safe_msg}`,
                to_email: "wodedge23@gmail.com"
            }}).then(function() {{
                console.log("Email sent successfully!");
            }}, function(error) {{
                console.log("Failed:", JSON.stringify(error));
            }});
        }};
        </script>
        """, height=0)
        st.success("✅ Feedback sent! Thank you.")

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888888; font-size: 14px; line-height: 1.6;'>
        Built with ❤️ by <a href='https://www.instagram.com/abdullrahhhh/' target='_blank' style='color: #4a90e2; text-decoration: none; font-weight: bold;'>Muhammad Abdullah Habib</a><br>
        <span style='font-size: 12px; color: #aaaaaa;'>
            Student at <a href='https://www.facebook.com/100063942365261' target='_blank' style='color: #4a90e2; text-decoration: none; font-weight: bold;'>DPS&C (Faisalabad)</a> | AI Development Initiative
        </span>
        <br><br>
        <div style='border-top: 1px dashed #444444; width: 40%; margin: 10px auto;'></div>
        <span style='font-size: 13px; color: #ffd700; font-weight: bold; letter-spacing: 1px;'>🌟 SPECIAL THANKS TO MY TESTERS 🌟</span><br>
        <div style='font-size: 13px; color: #bbbbbb; margin-top: 5px; font-family: monospace;'>
            Mohammad Rayan Hassan • Mustafa Ahmed • Dawood Faisal • Saleh Gill • Hashim Ali Gujjar
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

if st.session_state.checker_history:
    st.sidebar.title("History Panel 🕒")
    st.sidebar.write("Review previously analyzed sheets from this session:")
    
    for i, item in enumerate(st.session_state.checker_history):
        if st.sidebar.button(f"📄 {item['filename']}", key=f"hist_{i}"):
            st.sidebar.markdown(f"### Historical Review: {item['filename']}")
            st.sidebar.info(item['feedback'])