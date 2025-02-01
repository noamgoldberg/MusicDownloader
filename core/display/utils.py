from typing import Optional, Union, List
import streamlit as st
import streamlit.components.v1 as components


def display_dropdown(title: str, content: str):
    st.markdown(f"""
    <details>
    <summary>{title}</summary>
    <pre><code>{content}</code></pre>
    </details>
    """, unsafe_allow_html=True)
    
def display_embed_iframe(embed_url: Optional[str] = None):
    if embed_url is not None:
        iframe = f"""
        <iframe width="100%" height="166" scrolling="no" frameborder="no" allow="autoplay" 
        src="{embed_url}"></iframe>
        """
        components.html(iframe, height=200)

def display_labels(
    labels: Union[str, List[str]],
    num_cols: int = 6,
    font_size: int = 16,
    border_radius: int = 7,
):
    columns = st.columns(num_cols)
    labels = [labels] if isinstance(labels, str) else labels
    for i, label in enumerate(labels):
        with columns[i]:
            st.markdown(
                f'<button style="font-size:{font_size}px; border-radius:{border_radius}px;" '
                f'disabled><b>{label}</b></button>', unsafe_allow_html=True
            )

def display_urls_list(title: str, urls: List[str]):
    bullet_char = '- '
    formatted_urls = f"\n{bullet_char}".join(urls)  # Properly format URLs for bullet points
    if urls:
        display_dropdown(
            title=title,
            content=f"{bullet_char}{formatted_urls}"
        )
        st.write()

def display_captioned_image(
    *,
    image_url: str,
    hyperlink_url: str,
    title: str,
    caption: Optional[str] = None
):
    markdown = """
    <div style="text-align: center;">
        <a href="{hyperlink_url}" target="_blank">
            <img src="{image_url}" alt="{title}" style="max-width: 100%; height: auto;">
        </a>
        {caption}
    </div>
    """
    caption_markdown = f"""<p style="font-size: 16px; color: #555;">{caption}</p>""" if caption else ""
    markdown = markdown.format(
        hyperlink_url=hyperlink_url,
        image_url=image_url,
        title=title,
        caption=caption_markdown,
    )
    st.markdown(markdown, unsafe_allow_html=True)