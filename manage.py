
import streamlit as st
import sqlite3
import hashlib
import secrets
import re
from datetime import datetime

# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Smart Agriculture Management System",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB = "blogs.db"

CATEGORIES = [
    "Crop Management",
    "Soil Health",
    "Irrigation",
    "Organic Farming",
    "Agriculture Technology",
    "Weather",
    "General"
]

# ==========================================
# CUSTOM CSS - RESPONSIVE DESIGN
# ==========================================

st.markdown("""
<style>
.stApp {
    background: #e8f6ff;
    color: #111111;
}

section[data-testid="stSidebar"] {
    background: #c5eaff;
}

h1, h2, h3, p, label {
    color: #111111 !important;
}

.hero {
    background: linear-gradient(120deg,#9edcff,#e8f6ff);
    padding: 28px;
    border-radius: 18px;
    margin-bottom: 20px;
}

.hero h1 {
    color: #123c58 !important;
}

.card {
    background: white;
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #b7dff3;
    margin-bottom: 15px;
}

.stButton button {
    background: #87ceeb;
    color: #111111;
    border-radius: 10px;
    border: none;
    font-weight: bold;
}

.stTextInput input,
.stTextArea textarea {
    background: white;
    color: black;
}

@media (max-width: 768px) {
    .hero {
        padding: 15px;
    }
    .hero h1 {
        font-size: 25px;
    }
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# DATABASE CONNECTION
# ==========================================

def connect():
    return sqlite3.connect(DB)

def initialize_database():
    conn = connect()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS blogs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        summary TEXT,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()

initialize_database()

# ==========================================
# PASSWORD HASHING
# ==========================================

def hash_password(password, salt=None):

    if salt is None:
        salt = secrets.token_hex(16)

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        bytes.fromhex(salt),
        310000
    ).hex()

    return salt + ":" + hashed

def verify_password(password, stored):

    try:
        salt, original = stored.split(":")

        generated = hash_password(
            password, salt
        ).split(":")[1]

        return secrets.compare_digest(
            generated, original
        )

    except ValueError:
        return False

# ==========================================
# USER AUTHENTICATION
# ==========================================

def register_user(name, email, password):

    conn = connect()

    try:
        conn.execute("""
        INSERT INTO users(name,email,password)
        VALUES(?,?,?)
        """, (
            name,
            email.lower(),
            hash_password(password)
        ))

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()

def login_user(email, password):

    conn = connect()

    user = conn.execute("""
    SELECT id,name,email,password
    FROM users
    WHERE email=?
    """, (email.lower(),)).fetchone()

    conn.close()

    if user and verify_password(password, user[3]):
        return user

    return None

# ==========================================
# PROFILE MANAGEMENT
# ==========================================

def update_profile(user_id, name, email):

    conn = connect()

    try:
        conn.execute("""
        UPDATE users
        SET name=?, email=?
        WHERE id=?
        """, (
            name,
            email.lower(),
            user_id
        ))

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()

# ==========================================
# BLOG CRUD OPERATIONS
# ==========================================

def create_blog(user_id, title, category, summary, content):

    conn = connect()

    conn.execute("""
    INSERT INTO blogs
    (user_id,title,category,summary,content,created_at)
    VALUES(?,?,?,?,?,?)
    """, (
        user_id,
        title,
        category,
        summary,
        content,
        datetime.now().strftime("%d-%m-%Y %H:%M")
    ))

    conn.commit()
    conn.close()

def read_blogs(user_id):

    conn = connect()

    blogs = conn.execute("""
    SELECT id,title,category,summary,content,created_at
    FROM blogs
    WHERE user_id=?
    ORDER BY id DESC
    """, (user_id,)).fetchall()

    conn.close()
    return blogs

def update_blog(
    user_id, blog_id, title,
    category, summary, content
):

    conn = connect()

    conn.execute("""
    UPDATE blogs
    SET title=?, category=?, summary=?, content=?
    WHERE id=? AND user_id=?
    """, (
        title,
        category,
        summary,
        content,
        blog_id,
        user_id
    ))

    conn.commit()
    conn.close()

def delete_blog(user_id, blog_id):

    conn = connect()

    conn.execute("""
    DELETE FROM blogs
    WHERE id=? AND user_id=?
    """, (blog_id, user_id))

    conn.commit()
    conn.close()

# ==========================================
# SESSION MANAGEMENT
# ==========================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None

# ==========================================
# WEBSITE HEADER
# ==========================================

st.markdown("""
<div class="hero">
<h1>🌱 Smart Agriculture Management System</h1>
<h3>Smart Farming & Agriculture Blog Portal</h3>
<p>Manage agricultural knowledge with technology.</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# LOGIN AND REGISTRATION
# ==========================================

if not st.session_state.logged_in:

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        st.title("🔐 User Authentication")

        auth = st.radio(
            "Choose Account",
            ["Login", "Register"],
            horizontal=True
        )

        # REGISTRATION

        if auth == "Register":

            st.subheader("Create New Account")

            with st.form("register_form"):

                name = st.text_input("Full Name")
                email = st.text_input("Email Address")

                password = st.text_input(
                    "Password",
                    type="password"
                )

                confirm = st.text_input(
                    "Confirm Password",
                    type="password"
                )

                submit = st.form_submit_button(
                    "Register",
                    use_container_width=True
                )

                if submit:

                    if not name.strip():
                        st.error("Enter your name.")

                    elif not re.fullmatch(
                        r"[^@\s]+@[^@\s]+\.[^@\s]+",
                        email.strip()
                    ):
                        st.error("Enter a valid email.")

                    elif len(password) < 8:
                        st.error("Password must contain at least 8 characters.")

                    elif password != confirm:
                        st.error("Passwords do not match.")

                    else:

                        result = register_user(
                            name.strip(),
                            email.strip(),
                            password
                        )

                        if result:
                            st.success("Registration successful! Login now.")
                        else:
                            st.error("Email already registered.")

        # LOGIN

        else:

            st.subheader("Welcome Back")

            with st.form("login_form"):

                email = st.text_input("Email Address")

                password = st.text_input(
                    "Password",
                    type="password"
                )

                submit = st.form_submit_button(
                    "Login",
                    use_container_width=True
                )

                if submit:

                    user = login_user(
                        email.strip(),
                        password
                    )

                    if user:

                        st.session_state.logged_in = True

                        st.session_state.user = {
                            "id": user[0],
                            "name": user[1],
                            "email": user[2]
                        }

                        st.rerun()

                    else:
                        st.error("Invalid login credentials.")

# ==========================================
# AUTHENTICATED USER DASHBOARD
# ==========================================

else:

    user = st.session_state.user
    user_id = user["id"]

    st.sidebar.title("🌿 Main Dashboard")

    st.sidebar.success(
        "Welcome " + user["name"]
    )

    menu = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "Create Blog",
            "My Blogs",
            "Update Blog",
            "Delete Blog",
            "My Profile"
        ]
    )

    if st.sidebar.button(
        "Logout",
        use_container_width=True
    ):

        st.session_state.logged_in = False
        st.session_state.user = None

        st.rerun()

    blogs = read_blogs(user_id)

    # ======================================
    # DASHBOARD
    # ======================================

    if menu == "Dashboard":

        st.title("📊 Personal Dashboard")

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "My Total Blogs",
            len(blogs)
        )

        c2.metric(
            "My Categories",
            len(set(b[2] for b in blogs))
        )

        c3.metric(
            "Account Status",
            "Active"
        )

        st.subheader("🌾 Recent Blogs")

        for blog in blogs[:5]:

            st.markdown(
                f"""
                <div class="card">
                <h3>{blog[1]}</h3>
                <p>Category: {blog[2]}</p>
                <p>{blog[3] or ''}</p>
                <small>Published: {blog[5]}</small>
                </div>
                """,
                unsafe_allow_html=True
            )

        if not blogs:
            st.info("Create your first agriculture blog.")

    # ======================================
    # CREATE BLOG
    # ======================================

    elif menu == "Create Blog":

        st.title("✍️ Create Agriculture Blog")

        with st.form("create_blog"):

            title = st.text_input("Blog Title")

            category = st.selectbox(
                "Category",
                CATEGORIES
            )

            summary = st.text_area("Blog Summary")

            content = st.text_area(
                "Blog Content",
                height=200
            )

            submit = st.form_submit_button("Publish Blog")

            if submit:

                if title.strip() and content.strip():

                    create_blog(
                        user_id,
                        title.strip(),
                        category,
                        summary.strip(),
                        content.strip()
                    )

                    st.success("Blog published successfully!")
                    st.rerun()

                else:
                    st.error("Title and content are required.")

    # ======================================
    # VIEW / SEARCH BLOGS
    # ======================================

    elif menu == "My Blogs":

        st.title("📚 My Agriculture Blogs")

        search = st.text_input("Search Blogs")

        category_filter = st.selectbox(
            "Filter Category",
            ["All"] + CATEGORIES
        )

        for blog in blogs:

            searchable = (
                blog[1] + " " +
                (blog[3] or "") + " " +
                blog[4]
            ).lower()

            if search and search.lower() not in searchable:
                continue

            if category_filter != "All":
                if blog[2] != category_filter:
                    continue

            with st.expander("🌱 " + blog[1]):

                st.write("Category:", blog[2])
                st.write("Summary:", blog[3])
                st.write("Content:", blog[4])
                st.write("Date:", blog[5])

    # ======================================
    # UPDATE BLOG
    # ======================================

    elif menu == "Update Blog":

        st.title("✏️ Update My Blogs")

        if blogs:

            options = {
                f"{b[0]} - {b[1]}": b
                for b in blogs
            }

            selected = st.selectbox(
                "Select Blog",
                list(options.keys())
            )

            blog = options[selected]

            with st.form("update_form"):

                title = st.text_input(
                    "Blog Title",
                    value=blog[1]
                )

                category = st.selectbox(
                    "Category",
                    CATEGORIES,
                    index=CATEGORIES.index(blog[2])
                )

                summary = st.text_area(
                    "Summary",
                    value=blog[3] or ""
                )

                content = st.text_area(
                    "Content",
                    value=blog[4],
                    height=200
                )

                submit = st.form_submit_button("Save Changes")

                if submit:

                    if title.strip() and content.strip():

                        update_blog(
                            user_id,
                            blog[0],
                            title.strip(),
                            category,
                            summary.strip(),
                            content.strip()
                        )

                        st.success("Blog updated!")
                        st.rerun()

                    else:
                        st.error("Title and content are required.")

        else:
            st.info("No blogs available.")

    # ======================================
    # DELETE BLOG
    # ======================================

    elif menu == "Delete Blog":

        st.title("🗑️ Delete My Blogs")

        if blogs:

            options = {
                f"{b[0]} - {b[1]}": b
                for b in blogs
            }

            selected = st.selectbox(
                "Select Blog",
                list(options.keys())
            )

            blog = options[selected]

            st.warning(
                "Selected blog: " + blog[1]
            )

            confirm = st.checkbox(
                "I confirm that I want to delete this blog."
            )

            if st.button(
                "Delete Blog",
                disabled=not confirm
            ):

                delete_blog(user_id, blog[0])

                st.success("Blog deleted!")
                st.rerun()

        else:
            st.info("No blogs available.")

    # ======================================
    # USER PROFILE
    # ======================================

    elif menu == "My Profile":

        st.title("👤 My User Profile")

        with st.form("profile_form"):

            name = st.text_input(
                "Full Name",
                value=user["name"]
            )

            email = st.text_input(
                "Email",
                value=user["email"]
            )

            submit = st.form_submit_button(
                "Update Profile"
            )

            if submit:

                if not name.strip():
                    st.error("Enter your name.")

                elif not re.fullmatch(
                    r"[^@\s]+@[^@\s]+\.[^@\s]+",
                    email.strip()
                ):
                    st.error("Enter a valid email.")

                else:

                    result = update_profile(
                        user_id,
                        name.strip(),
                        email.strip()
                    )

                    if result:

                        st.session_state.user["name"] = name.strip()
                        st.session_state.user["email"] = email.strip().lower()

                        st.success("Profile updated!")
                        st.rerun()

                    else:
                        st.error("Email already exists.")

        st.divider()

        st.write("User ID:", user_id)
        st.write("Account Email:", user["email"])

# ==========================================
# FOOTER
# ==========================================

st.divider()

st.markdown("""
<center>
🌱 Smart Agriculture Management System<br>
Agriculture Blog Management Portal
</center>
""", unsafe_allow_html=True)
