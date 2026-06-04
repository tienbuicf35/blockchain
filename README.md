# Ứng dụng sàng lọc bệnh da liễu

Project này là app demo sàng lọc bệnh da từ ảnh, kết hợp checklist triệu chứng, chẩn đoán gợi ý và lời khuyên chăm sóc ban đầu.

## Ý tưởng

Thay vì chỉ trả về top-k dự đoán từ ảnh, app chạy quy trình 2 bước:

1. Phân loại ảnh tổn thương da.
2. Kết hợp câu trả lời nhanh về triệu chứng để đưa ra mức độ cần ưu tiên xem lại.

Kết quả screening gồm nhãn bệnh, chẩn đoán gợi ý, mô tả ngắn, dấu hiệu cần đi khám, lời khuyên chăm sóc và cảnh báo rằng công cụ không thay thế bác sĩ.

## Tính năng

- UI upload ảnh + checklist triệu chứng bằng tiếng Việt có dấu.
- API FastAPI cho `predict`, `screen` và ledger.
- CLI hỗ trợ `predict` và `screen`.
- Dùng mô hình local `skin-disease-classifier`.
- Có phân loại mức độ nguy hiểm: `low`, `moderate`, `high`.
- Có hybrid blockchain: off-chain lưu payload dự đoán, on-chain neo hash và metadata.

## Nhãn bệnh

- `AK` - Dày sừng ánh sáng
- `BCC` - Ung thư biểu mô tế bào đáy
- `BKL` - Dày sừng lành tính
- `DF` - U xơ da
- `MEL` - U hắc tố da
- `NV` - Nốt ruồi sắc tố
- `SCC` - Ung thư biểu mô tế bào vảy
- `VASC` - Tổn thương mạch máu

## Cài đặt

```bash
pip install -r requirements.txt
```

## Chạy web

```bash
uvicorn app.main:app --reload
```

Mở:

```text
http://127.0.0.1:8000/
```

## Chạy CLI

Chỉ dự đoán:

```bash
python cli.py --image path/to/image.jpg
```

Screening có triệu chứng:

```bash
python cli.py --image path/to/image.jpg --mode screen --itch yes --bleed no --grow yes
```

## API

- `GET /`
- `GET /health`
- `POST /predict`
- `POST /screen`
- `POST /screen-ui`
- `GET /ledger`
- `GET /ledger/ui`
- `GET /ledger/validate`
- `GET /ledger/export.json`
- `GET /ledger/export.csv`

## Ghi chú y khoa

Đây chỉ là công cụ nghiên cứu/demo, không dùng làm chẩn đoán y khoa chính thức. Nếu tổn thương đau, chảy máu, loét, đổi màu, lớn nhanh hoặc khiến bạn lo lắng, hãy đi khám bác sĩ da liễu.

## Kiến trúc blockchain

- Off-chain: lưu dữ liệu đầy đủ của từng lần screening, gồm ảnh sha256, model, top-k và predictions.
- On-chain: lưu anchor block, hash liên kết, chữ ký wallet và metadata cần kiểm tra.
- Backend mặc định vẫn hoạt động local; nếu set `LEDGER_BACKEND=evm` và cấu hình provider / contract / private key, app sẽ ghi anchor lên smart contract EVM thật.

### Cấu hình EVM

Bạn cần deploy contract trong `contracts/PredictionLedger.sol` lên một blockchain EVM compatible như Ethereum, Sepolia, Polygon, Base hoặc localhost chain.

Biến môi trường cần thiết:

- `WEB3_PROVIDER_URI`: RPC endpoint
- `LEDGER_CONTRACT_ADDRESS`: địa chỉ contract đã deploy
- `LEDGER_PRIVATE_KEY`: private key của wallet ký giao dịch
- `LEDGER_SIGNER_ADDRESS`: địa chỉ wallet ký, nếu muốn ép khớp
- `LEDGER_BACKEND=evm`: bật blockchain thật

Nếu không có các biến này, app sẽ tiếp tục dùng local JSON ledger để phục vụ demo và test.

### Cấu hình Hyperledger Fabric

Repo có thêm backend `fabric` để neo hash kết quả screening lên Hyperledger Fabric, trong khi ảnh và payload y tế vẫn nằm off-chain trong `data/offchain/prediction_payloads.json`.

Chạy app ở chế độ Fabric local-mirror:

```bash
set LEDGER_BACKEND=fabric
set FABRIC_MSP_ID=Org1MSP
uvicorn app.main:app --reload
```

Chế độ này vẫn chạy được khi chưa có Fabric network thật. Ledger sẽ gắn `storage=fabric-private-data+off-chain-json` để mô phỏng kiến trúc Fabric + off-chain.

Khi đã có Fabric network và đã cài Fabric peer CLI, cấu hình thêm:

```bash
set LEDGER_BACKEND=fabric
set FABRIC_CHANNEL_NAME=mychannel
set FABRIC_CHAINCODE_NAME=prediction-ledger
set FABRIC_PEER_COMMAND=peer
set FABRIC_MSP_ID=Org1MSP
```

Nếu muốn bắt buộc giao dịch Fabric phải thành công, thêm:

```bash
set FABRIC_REQUIRE_COMMIT=true
```

Chaincode mẫu nằm trong `contracts/fabric`. Hàm chính:

- `RecordPredictionAnchor(index, timestamp, source, offchainRecordID, payloadHash, previousHash, hash, signature, storage)`
- `GetPredictionAnchor(index)`
- `GetHead()`

Dữ liệu không nên đưa lên Fabric: ảnh bệnh da, tên bệnh nhân, thông tin định danh, hồ sơ y tế đầy đủ. Fabric chỉ nên lưu hash, metadata audit, MSP của bên ghi và tham chiếu off-chain.
