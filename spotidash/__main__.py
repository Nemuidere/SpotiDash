from spotidash import SpotiDash

if __name__ == "__main__":
    app = SpotiDash()
    app.run(debug=True, host="0.0.0.0", port=8050)
