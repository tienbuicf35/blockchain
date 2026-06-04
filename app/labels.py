LABEL_MAP = {
    "AK": "Dày sừng ánh sáng",
    "BCC": "Ung thư biểu mô tế bào đáy",
    "BKL": "Dày sừng lành tính",
    "DF": "U xơ da",
    "MEL": "U hắc tố da",
    "NV": "Nốt ruồi sắc tố",
    "SCC": "Ung thư biểu mô tế bào vảy",
    "VASC": "Tổn thương mạch máu",
}


DISEASE_GUIDANCE = {
    "AK": {
        "diagnosis": "Nghi ngờ dày sừng ánh sáng",
        "overview": "Tổn thương thô ráp, bong vảy do tác hại ánh nắng kéo dài; một phần nhỏ có thể tiến triển thành ung thư tế bào vảy.",
        "advice": [
            "Che nắng kỹ, dùng kem chống nắng phổ rộng SPF 30+ mỗi ngày.",
            "Đặt lịch khám da liễu để xác nhận và cân nhắc điều trị nếu tổn thương dai dẳng.",
            "Theo dõi ảnh mỗi 4-6 tuần nếu chưa thể đi khám ngay.",
        ],
        "warning_signs": [
            "Tổn thương đau, loét, chảy máu hoặc dày lên nhanh.",
            "Có nhiều mảng sần ở vùng thường phơi nắng.",
        ],
    },
    "BCC": {
        "diagnosis": "Nghi ngờ ung thư biểu mô tế bào đáy",
        "overview": "Dạng ung thư da thường gặp, phát triển chậm nhưng có thể xâm lấn mô xung quanh nếu để lâu.",
        "advice": [
            "Nên khám da liễu sớm để soi da và sinh thiết khi cần.",
            "Không tự cạy, đốt hoặc bôi thuốc không rõ nguồn gốc.",
            "Che nắng vùng tổn thương và ghi lại kích thước, màu sắc, bờ tổn thương.",
        ],
        "warning_signs": [
            "Nốt bóng, viền ngọc trai, loét lâu lành hoặc chảy máu tái diễn.",
            "Tổn thương ở mặt, mũi, mí mắt, tai hoặc môi.",
        ],
    },
    "BKL": {
        "diagnosis": "Gợi ý dày sừng lành tính",
        "overview": "Thường là tổn thương lành tính dạng mảng sáp hoặc sần, hay gặp ở người trưởng thành.",
        "advice": [
            "Theo dõi nếu tổn thương ổn định, không đau, không chảy máu.",
            "Khám da liễu nếu tổn thương mới xuất hiện, đổi màu, tăng kích thước hoặc gây khó chịu.",
            "Tránh ma sát mạnh và tránh tự bóc gỡ.",
        ],
        "warning_signs": [
            "Tăng nhanh, chảy máu, loét hoặc màu sắc không đều.",
            "Khó phân biệt với nốt ruồi thay đổi hoặc u hắc tố.",
        ],
    },
    "DF": {
        "diagnosis": "Gợi ý u xơ da",
        "overview": "Tổn thương lành tính dạng nốt chắc, có thể lõm nhẹ khi bóp hai bên.",
        "advice": [
            "Có thể theo dõi nếu nốt ổn định và không gây triệu chứng.",
            "Khám da liễu nếu nốt đau, lớn nhanh, đổi màu hoặc ảnh hưởng sinh hoạt.",
            "Không tự nặn hoặc chích vì dễ nhiễm trùng và sẹo.",
        ],
        "warning_signs": [
            "Đau tăng, chảy máu, loét hoặc phát triển nhanh.",
            "Tổn thương có bờ không đều hoặc màu sắc thay đổi rõ.",
        ],
    },
    "MEL": {
        "diagnosis": "Nghi ngờ u hắc tố da",
        "overview": "U hắc tố là ung thư da nguy hiểm, cần được đánh giá sớm, đặc biệt khi tổn thương thay đổi theo quy tắc ABCDE.",
        "advice": [
            "Ưu tiên khám da liễu càng sớm càng tốt để soi da và sinh thiết nếu cần.",
            "Chụp ảnh rõ nét, đo kích thước và tránh trì hoãn nếu tổn thương đang lớn nhanh.",
            "Kiểm tra thêm các nốt ruồi khác trên cơ thể.",
        ],
        "warning_signs": [
            "Bất đối xứng, bờ không đều, nhiều màu, đường kính lớn hoặc thay đổi nhanh.",
            "Ngứa, đau, chảy máu, loét hoặc có nốt vệ tinh xung quanh.",
        ],
    },
    "NV": {
        "diagnosis": "Gợi ý nốt ruồi sắc tố",
        "overview": "Nốt ruồi sắc tố thường lành tính, nhưng cần theo dõi nếu có thay đổi về hình dạng, màu sắc hoặc kích thước.",
        "advice": [
            "Theo dõi định kỳ bằng ảnh trong cùng điều kiện ánh sáng.",
            "Dùng chống nắng và tránh cháy nắng.",
            "Khám da liễu nếu nốt ruồi khác biệt rõ so với các nốt còn lại.",
        ],
        "warning_signs": [
            "Thay đổi nhanh, bất đối xứng, bờ nham nhở hoặc nhiều màu.",
            "Chảy máu, đau, ngứa kéo dài hoặc loét.",
        ],
    },
    "SCC": {
        "diagnosis": "Nghi ngờ ung thư biểu mô tế bào vảy",
        "overview": "Ung thư tế bào vảy có thể phát triển từ vùng da tổn thương do nắng hoặc vết thương mạn tính và cần đánh giá y khoa.",
        "advice": [
            "Nên khám da liễu sớm, nhất là khi tổn thương dày, đau hoặc loét.",
            "Giữ vùng tổn thương sạch, tránh cạy gãi và tránh nắng.",
            "Ghi nhận thời gian xuất hiện, tốc độ lớn lên và triệu chứng kèm theo.",
        ],
        "warning_signs": [
            "Mảng/nốt dày sừng, loét lâu lành, đau hoặc chảy máu.",
            "Tổn thương ở môi, tai, bàn tay hoặc trên sẹo/vết thương cũ.",
        ],
    },
    "VASC": {
        "diagnosis": "Gợi ý tổn thương mạch máu",
        "overview": "Có thể là nhóm tổn thương liên quan mạch máu như u máu hoặc dị dạng mạch; đa số lành tính nhưng vẫn cần theo dõi bối cảnh lâm sàng.",
        "advice": [
            "Theo dõi kích thước, màu sắc và khả năng chảy máu.",
            "Khám da liễu nếu tổn thương mới xuất hiện, lan nhanh hoặc dễ chảy máu.",
            "Tránh va chạm mạnh lên vùng tổn thương.",
        ],
        "warning_signs": [
            "Chảy máu nhiều, đau, loét hoặc tăng kích thước nhanh.",
            "Tổn thương xuất hiện nhiều nơi hoặc kèm bầm tím bất thường.",
        ],
    },
}


MEDICAL_DISCLAIMER = (
    "Kết quả chỉ hỗ trợ sàng lọc bằng AI, không thay thế chẩn đoán của bác sĩ. "
    "Nếu tổn thương đau, chảy máu, loét, đổi màu hoặc lớn nhanh, hãy đi khám da liễu."
)
