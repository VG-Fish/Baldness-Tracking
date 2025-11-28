import random
import time

import av
import cv2
import streamlit as st
from streamlit_extras.floating_button import floating_button
from streamlit_extras.let_it_rain import rain
from streamlit_webrtc import WebRtcMode, webrtc_streamer

import database

WELCOME_TEXT = "WELCOME TO BALDY THE BALDMAN'S BALDNESS TRACKER!"

st.session_state.setdefault("greeting_finished", False)
st.session_state.setdefault("init_db", False)

if not st.session_state.init_db:
    database.init_db()
    st.session_state.init_db = True


def stream_data():
    yield "# "
    for word in WELCOME_TEXT.split(" "):
        yield f"{word} "
        time.sleep(random.random() * 0.25)
    yield "\n"


if not st.session_state.greeting_finished:
    st.write_stream(stream_data, cursor="👨‍🦲👨‍🦲👨‍🦲👨‍🦲👨‍🦲")
    st.session_state.greeting_finished = True
else:
    st.markdown(f"# {WELCOME_TEXT}")

st.text(
    """
    To use this app, select your camera input device or click start and align your nose to the red crosshair.
    Then, if you are satisfied, save the image and view all saved images by clicking the "Show all images" button in the bottom right.
    """
)


class CrosshairProcessor:
    def __init__(self):
        self.latest_frame_bgr = None

    @staticmethod
    def add_crosshair(image) -> av.VideoFrame:
        height, width = image.shape[:2]
        center_x, center_y = width // 2, height // 2
        size, thickness, color = 20, 2, (0, 0, 255)
        cv2.line(
            image,
            (center_x - size, center_y),
            (center_x + size, center_y),
            color,
            thickness,
        )
        cv2.line(
            image,
            (center_x, center_y - size),
            (center_x, center_y + size),
            color,
            thickness,
        )
        return av.VideoFrame.from_ndarray(image, format="bgr24")

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        image = frame.to_ndarray(format="bgr24")
        self.latest_frame_bgr = image.copy()
        return CrosshairProcessor.add_crosshair(image)


ctx = webrtc_streamer(  # pyright: ignore[reportCallIssue]
    key="streamer",
    mode=WebRtcMode.SENDRECV,
    video_processor_factory=CrosshairProcessor,  # pyright: ignore[reportArgumentType]
    media_stream_constraints={"video": True, "audio": False},
    sendback_audio=False,
    async_processing=False,
)


@st.dialog("Captured Image")
def captured_image_dialog(image):
    st.image(image, caption="Snapshot")
    save = st.button("Save Image?")
    if save:
        bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        database.save_image_to_db(bgr)
        st.rerun()


snapshot = st.button("📸 Take snapshot")

if snapshot and ctx and ctx.video_processor:
    frame_bgr = ctx.video_processor.latest_frame_bgr
    if frame_bgr is not None:
        rgb = CrosshairProcessor.add_crosshair(frame_bgr)
        rgb = rgb.to_ndarray(format="bgr24")
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        captured_image_dialog(rgb)
    else:
        st.warning("No frame captured yet. Wait a moment for the stream to start.")
elif snapshot:
    st.warning("Stream is not running. Start the camera first.")

if floating_button("Show all images"):
    st.subheader("Your images from oldest to newest:")
    rows = database.load_images_from_db()
    amount_of_columns = 3
    cols = st.columns(amount_of_columns)
    for idx, (date, image) in enumerate(reversed(rows)):
        with cols[idx % amount_of_columns]:
            st.image(
                image,
                width="stretch",
                caption=f"Date taken: {date.partition('    ')[0]}",
            )

rain(
    emoji="👨‍🦲",
    font_size=54,
    falling_speed=5,
    animation_length="infinite",
)
