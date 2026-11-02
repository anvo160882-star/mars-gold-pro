# M.A.R.S. GOLD PRO — Streamlit rebuild

## Giữ nguyên nền tảng
- Streamlit Community Cloud
- GitHub repository hiện tại
- Không cần React, Node.js hay server riêng

## Cài đặt / deploy
1. Giải nén ZIP trên Mac.
2. Mở repository GitHub `mars-gold-pro`.
3. Thay nội dung `app.py` bằng file `app.py` trong gói.
4. Thay nội dung `requirements.txt` bằng file tương ứng.
5. Commit changes và chờ Streamlit tự deploy.

## 5 workspace
1. Market Analysis
2. Probability Zones
3. 3D Forecast
4. Trade Intelligence
5. Data Health

## Nguồn dữ liệu và giới hạn được công khai
- XAUS public API: spot reference, daily history, sampled intraday.
- XAUS spot là giá tham chiếu, không phải giá khớp lệnh broker.
- Nếu daily API không trả Open, daily candle Open được tái dựng từ previous close và được ghi chú rõ.
- Không giả lập nến H4/H1/M15. Muốn phân tích các khung này, tải CSV OHLC từ cùng một broker/provider qua sidebar.
- Probability Zones là phân vị lợi suất lịch sử, chưa phải xác suất dự báo đã calibration.
- 3D Forecast là volatility envelope minh họa dựa trên realized volatility, không phải ML forecast.
- Trade Intelligence mặc định NO TRADE; không phát BUY/SELL trước khi có dữ liệu đồng nhất và walk-forward validation.
- Không tạo spot volume giả.

## CSV format
Tên cột được chấp nhận:
- Timestamp: `time`, `timestamp`, `date`, `datetime`
- OHLC: `open`, `high`, `low`, `close`
- Volume (optional): `volume`, `tick_volume`

CSV cần ít nhất 80 nến để hiện provisional EMA regime; nên dùng 500+ nến cho phân tích cấu trúc. Tất cả H4/H1/M15 nên cùng nguồn giá và timestamp UTC.

## Chú ý
Gói này kết nối XAUS API khi ứng dụng chạy. Nếu nguồn API không phản hồi hoặc trả dữ liệu stale, dashboard sẽ hiển thị trạng thái tương ứng; không có dữ liệu giả dự phòng.
