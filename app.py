from flask import Flask, render_template, render_template_string, request, redirect, url_for
import pandas as pd
import matplotlib.pyplot as plt 
import io, base64
import os 

app = Flask(__name__)

# đọc dữ liệu từ CSV
def load_data():
    return pd.read_csv("diem_thi.csv", encoding="utf-8")


# Lưu lại dữ liệu vào CSV
def save_data(df):
    df.to_csv("diem_thi.csv", index=False)

@app.route("/")
def index():
    df = load_data()
    return render_template("index.html", tables=df.to_html(classes="table table-bordered", index=False))

@app.route("/chart")
def chart():
    df = load_data()
    df["DiemTB"] = df[["Toan", "Van", "Anh"]].mean(axis=1)
    
    
    #vẽ biểu đồ
    img = io.BytesIO()
    plt.figure(figsize=(6,4))
    plt.hist(df["DiemTB"], bins=5, edgecolor="black")
    plt.title("Phân bố điểm trung bình học sinh")
    plt.xlabel("Điểm")
    plt.ylabel("Số lượng")
    plt.savefig(img, format="png")
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return render_template("chart.html", plot_url=plot_url)

@app.route("/chart/<subject>")
def chart_subject(subject):
    df = load_data()

    if subject not in ["Toan", "Van", "Anh"]:
        return f"Môn {subject} không hợp lệ!"

    # Vẽ biểu đồ cho môn được chọn
    img = io.BytesIO()
    plt.figure(figsize=(6,4))
    plt.hist(df[subject], bins=5, edgecolor="black", color="skyblue")
    plt.title(f"Phân bố điểm môn {subject}")
    plt.xlabel("Điểm")
    plt.ylabel("Số lượng học sinh")
    plt.savefig(img, format="png")
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return render_template("chart_subject.html", subject=subject, plot_url=plot_url)

# Thêm học sinh
@app.route("/add", methods=["GET", "POST"])
def add():
    df = load_data()
    message = ""
    category = ""

    if request.method == "POST":
        mahs = request.form["MaHS"]
        tenhs = request.form["HoTen"]
        toan = int(request.form["Toan"])
        van = int(request.form["Van"])
        anh = int(request.form["Anh"])

        # Kiểm tra nếu Mã HS đã tồn tại
        if mahs in df["MaHS"].astype(str).values:
            message = f"❌ Mã HS {mahs} đã tồn tại, không thể thêm!"
            category = "error"
        else:
            # Thêm học sinh mới
            new_data = {"MaHS": mahs, "HoTen": hoten, "Toan": toan, "Van": van, "Anh": anh}
            df = df.append(new_data, ignore_index=True)
            save_data(df)
            message = f"✅ Đã thêm học sinh mới: {hoten} (Mã HS: {mahs})"
            category = "success"

    return render_template(
        "add.html",
        tables=df.to_html(classes="table table-bordered", index=False),
        message=message,
        category=category
    )


# hàm cập nhật  học sinh
@app.route('/edit', methods=['GET', 'POST'])
def edit_student():
    message = ""
    df = pd.read_csv("diem_thi.csv")
    if request.method == 'POST':
        MaHS = request.form['MaHS']
        HoTen = request.form['HoTen']
        Toan = request.form['Toan']
        Van = request.form['Van']
        Anh = request.form['Anh']

        # Kiểm tra xem Mã HS có tồn tại không
        if MaHS in df['MaHS'].values:
            # Cập nhật thông tin theo Mã HS
            df.loc[df['MaHS'] == MaHS, ['HoTen', 'Toan', 'Van', 'Anh']] = [HoTen, Toan, Van, Anh]
            df.to_csv("diem_thi.csv", index=False)
            message = " Đã cập nhật học sinh có Mã HS: " + MaHS
        else:
            message = " Không tìm thấy học sinh có Mã HS: " + MaHS

    # Đọc lại dữ liệu sau khi cập nhật
    df = pd.read_csv("diem_thi.csv")
    return render_template(
        "edit.html",
        tables=df.to_html(classes="table table-bordered", index=False),
        message=message
    )

# hàm xóa học sinh
@app.route("/delete", methods=["GET", "POST"])
def delete():
    df = load_data()
    message = ""

    if request.method == "POST":
        mahs = request.form["MaHS"]

        # Kiểm tra học sinh có tồn tại không
        if mahs in df["MaHS"].astype(str).values:
            df = df[df["MaHS"].astype(str) != mahs]  # xoá hàng có MaHS khớp
            save_data(df)
            message = f"✅ Đã xoá học sinh có Mã HS = {mahs}"
        else:
            message = f"⚠️ Không tìm thấy học sinh có Mã HS = {mahs}"

    return render_template("delete.html", tables=df.to_html(classes="table table-bordered", index=False), message=message)


# hàm tìm kiếm học sinh
@app.route("/search", methods=["GET", "POST"])
def search():
    df = load_data()
    result = None
    keyword = ""
    message = ""  # thêm biến thông báo

    if request.method == "POST":
        keyword = request.form["keyword"].strip().lower()

        # Tìm theo Mã HS hoặc HoTen (không phân biệt hoa thường)
        result = df[
            (df["MaHS"].astype(str).str.lower() == keyword) |
            (df["HoTen"].str.lower().str.contains(keyword))
        ]

        # Nếu không tìm thấy thì gán thông báo
        if result.empty:
            message = f"❌ Không tìm thấy học sinh với từ khóa: {keyword}"
            result = None
        else:
            message = f"✅ Tìm thấy {len(result)} kết quả cho từ khóa: {keyword}"

    return render_template(
        "search.html",
        tables=df.to_html(classes="table table-bordered", index=False),
        result=None if result is None else result.to_html(classes="table table-bordered", index=False),
        keyword=keyword,
        message=message   # truyền thông báo sang HTML
    )

# hàm tìm kiếm học sinh có điểm cao nhất
@app.route("/top_student")
def top_student():
    df = load_data()
    df["DiemTB"] = df[["Toan", "Van", "Anh"]].mean(axis=1)  # Tính điểm trung bình

    # Học sinh có điểm trung bình cao nhất
    top = df.loc[df["DiemTB"].idxmax()]

    return render_template(
        "top_student.html",
        student=top.to_dict()
    )

# hàm tìm kiếm học sinh có điểm thấp nhất
@app.route("/low_student")
def low_student():
    df = load_data()
    df["DiemTB"] = df[["Toan", "Van", "Anh"]].mean(axis=1)  # Tính GPA

    # Học sinh có GPA thấp nhất
    low = df.loc[df["DiemTB"].idxmin()]

    return render_template(
        "low_student.html",
        student=low.to_dict()
    )

# hàm hiển thị danh sách học sinh với điểm trung bình
@app.route("/students")
def students_list():
    df = load_data()  # Đọc dữ liệu CSV
    df["DiemTB"] = df[["Toan", "Van", "Anh"]].mean(axis=1)
    
    # Chuyển DataFrame thành HTML table
    table_html = df.to_html(classes="table table-bordered", index=False)
    
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>Danh sách học sinh</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    </head>
    <body>
        <h1>Danh sách học sinh</h1>
        {{ table|safe }}
        <br />
<button onclick="window.location.href='/'">Quay lại</button>
    </body>
    </html>
    """, table=table_html)
# xuất file ra excel
from flask import send_file
import io

@app.route("/excel")
def excel():
    df = load_data()

    # Xuất DataFrame ra Excel trong bộ nhớ (không cần lưu file tạm)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="DiemThi")
    output.seek(0)

    return send_file(
        output,
        download_name="diem_thi.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Lấy PORT từ Render
    app.run(host="0.0.0.0", port=port, debug=False)
