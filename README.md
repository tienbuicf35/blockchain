# 🩺 Ứng dụng sàng lọc bệnh da liễu sử dụng AI và Hybrid Blockchain

Project này là hệ thống hỗ trợ sàng lọc bệnh da liễu từ hình ảnh tổn thương da, kết hợp giữa Trí tuệ nhân tạo (AI), Blockchain Hybrid và cơ chế lưu trữ Off-chain nhằm tăng độ tin cậy, khả năng truy vết và bảo vệ tính toàn vẹn dữ liệu y tế.

---

## 📌 Mục tiêu đề tài

- Phân tích ảnh tổn thương da bằng AI.
- Hỗ trợ sàng lọc ban đầu cho người dùng.
- Kết hợp triệu chứng lâm sàng để tăng độ tin cậy.
- Áp dụng Blockchain Hybrid để lưu vết kết quả.
- Đảm bảo tính toàn vẹn dữ liệu bằng SHA-256.
- Hỗ trợ truy xuất lịch sử sàng lọc.

---
## 📄 Poster đề tài

![Poster](Poster%20%E1%BA%A2nh%20ch%E1%BB%A5p%20m%C3%A0n%20h%C3%ACnh%202026-06-04%20142420.png)
# 🖥️ Demo giao diện

## Trang chủ

![Home](aa/Ảnh%20chụp%20màn%20hình%202026-06-04%20133821.png)

---

## Giao diện tải ảnh và nhập triệu chứng

![Screening](aa/Ảnh%20chụp%20màn%20hình%202026-06-04%20134027.png)

---

## Kết quả phân tích AI

![Result](aa/Ảnh%20chụp%20màn%20hình%202026-06-04%20134059.png)

---

## Sổ cái Blockchain Hybrid

![Ledger](aa/Ảnh%20chụp%20màn%20hình%202026-06-04%20134121.png)

---

# ⚙️ Ý tưởng hoạt động

Thay vì chỉ trả về top-k dự đoán từ ảnh, ứng dụng thực hiện quy trình nhiều bước:

1. Người dùng tải ảnh tổn thương da.
2. AI thực hiện phân loại bệnh.
3. Người dùng trả lời bảng câu hỏi triệu chứng.
4. Hệ thống đánh giá mức độ nguy cơ.
5. Sinh báo cáo screening.
6. Tạo SHA-256 Hash.
7. Lưu hồ sơ chi tiết Off-chain.
8. Ghi Hash và Metadata lên Blockchain.

---

# 🏗️ Kiến trúc hệ thống

```text
Người dùng
      │
      ▼
 Upload ảnh
      │
      ▼
 AI Classification
      │
      ▼
 Screening Engine
      │
 ┌────┴─────────┐
 │              │
 ▼              ▼
Off-chain    Blockchain
 Storage       Ledger
 │              │
 ▼              ▼
Payload      Hash + Metadata
```

---

## Sơ đồ kiến trúc

Sơ đồ luồng tổng quan được thể hiện trong khối kiến trúc ở trên.

---

# 🤖 Công nghệ sử dụng

## AI

- PyTorch
- HuggingFace Transformers
- AutoImageProcessor
- AutoModelForImageClassification

## Backend

- FastAPI
- Uvicorn
- Jinja2
- Pydantic

## Blockchain

- SHA-256
- Hybrid Blockchain
- Solidity
- Ethereum Compatible Networks
- Hyperledger Fabric

## Lưu trữ

- Off-chain Storage
- Local JSON Storage
- Blockchain Ledger

---

# ✨ Tính năng

- Upload ảnh tổn thương da.
- AI phân tích bệnh da.
- Hỗ trợ checklist triệu chứng.
- Đánh giá mức độ nguy hiểm.
- Sinh báo cáo screening.
- Hybrid Blockchain lưu vết lịch sử.
- Kiểm tra tính toàn vẹn dữ liệu.
- Xuất JSON và CSV.
- Hỗ trợ REST API.
- Hỗ trợ CLI.

---

# 🏥 Các bệnh hỗ trợ

| Mã | Tên bệnh |
|-----|-----------|
| AK | Dày sừng ánh sáng |
| BCC | Ung thư biểu mô tế bào đáy |
| BKL | Dày sừng lành tính |
| DF | U xơ da |
| MEL | U hắc tố da |
| NV | Nốt ruồi sắc tố |
| SCC | Ung thư biểu mô tế bào vảy |
| VASC | Tổn thương mạch máu |

---

# 🔗 Blockchain Hybrid

## Off-chain

Lưu trữ:

- Hình ảnh tổn thương da
- Payload dự đoán
- Kết quả screening
- Xác suất dự đoán
- Thông tin y tế chi tiết

## On-chain

Lưu trữ:

- Record ID
- SHA-256 Hash
- Previous Hash
- Timestamp
- Metadata
- Medical Summary
- Digital Signature

## Lợi ích

- Chống sửa đổi dữ liệu.
- Truy vết lịch sử screening.
- Kiểm tra tính toàn vẹn dữ liệu.
- Tăng độ tin cậy cho hệ thống.
- Giảm tải cho Blockchain.

---

# 📡 API

## Health Check

```http
GET /health
```

## Predict

```http
POST /predict
```

## Screen

```http
POST /screen
```

## Ledger

```http
GET /ledger
```

## Ledger UI

```http
GET /ledger/ui
```

## Validate Ledger

```http
GET /ledger/validate
```

## Export JSON

```http
GET /ledger/export.json
```

## Export CSV

```http
GET /ledger/export.csv
```

---

# 📦 Cài đặt

```bash
pip install -r requirements.txt
```

---

# 🚀 Chạy ứng dụng

## Web

```bash
uvicorn app.main:app --reload
```

Mở trình duyệt:

```text
http://127.0.0.1:8000/
```

---

## CLI

Dự đoán ảnh:

```bash
python cli.py --image path/to/image.jpg
```

Screening:

```bash
python cli.py --image path/to/image.jpg --mode screen --itch yes --bleed no --grow yes
```

---

# ⛓️ Smart Contract EVM

Contract:

```text
contracts/PredictionLedger.sol
```

Biến môi trường:

```env
LEDGER_BACKEND=evm
WEB3_PROVIDER_URI=
LEDGER_CONTRACT_ADDRESS=
LEDGER_PRIVATE_KEY=
LEDGER_SIGNER_ADDRESS=
```

Hỗ trợ:

- Ethereum
- Sepolia
- Polygon
- Base
- Local Blockchain

---

# 🏢 Hyperledger Fabric

```env
LEDGER_BACKEND=fabric
FABRIC_CHANNEL_NAME=mychannel
FABRIC_CHAINCODE_NAME=prediction-ledger
FABRIC_MSP_ID=Org1MSP
```

---

# 🔒 Bảo mật

- SHA-256 Integrity Check
- Blockchain Hash Chaining
- Immutable Ledger
- Medical Record Verification
- Audit Trail

---

# 📊 Kết quả mẫu

| Thành phần | Trạng thái |
|------------|------------|
| AI Classification | ✅ |
| Screening Engine | ✅ |
| SHA-256 | ✅ |
| Hybrid Blockchain | ✅ |
| Ledger Validation | ✅ |
| CSV Export | ✅ |
| JSON Export | ✅ |

---

# 🔮 Hướng phát triển

- Tích hợp IPFS thực tế.
- Triển khai Blockchain Mainnet.
- Xây dựng Mobile App.
- Tích hợp Telemedicine.
- Hỗ trợ nhiều bệnh da liễu hơn.
- Kết nối hồ sơ bệnh án điện tử.

---

# ⚠️ Ghi chú y khoa

Đây là công cụ hỗ trợ nghiên cứu và sàng lọc ban đầu. Kết quả chỉ mang tính tham khảo và không thay thế cho chẩn đoán của bác sĩ chuyên khoa da liễu.

Nếu tổn thương da có dấu hiệu chảy máu, loét, đổi màu, đau hoặc phát triển nhanh, người dùng nên đến cơ sở y tế để được thăm khám và điều trị kịp thời.

---

# 👨‍💻 Tác giả

Đề tài môn học: Xử lý ảnh / AI / Blockchain

Sinh viên thực hiện: [Tên của bạn]

Năm thực hiện: 2025–2026

Chaincode mẫu nằm trong `contracts/fabric`. Hàm chính:

- `RecordPredictionAnchor(index, timestamp, source, offchainRecordID, payloadHash, previousHash, hash, signature, storage)`
- `GetPredictionAnchor(index)`
- `GetHead()`

Dữ liệu không nên đưa lên Fabric: ảnh bệnh da, tên bệnh nhân, thông tin định danh, hồ sơ y tế đầy đủ. Fabric chỉ nên lưu hash, metadata audit, MSP của bên ghi và tham chiếu off-chain.
