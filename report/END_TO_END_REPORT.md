# End-to-End Run Report

## Summary

- Total test cases: 6
- Chatbot success: 6/6
- ReAct agent success: 6/6
- LLM requests tracked: 15
- Total tokens estimated: 1961
- Average tokens/request: 130.73
- Average completion/prompt ratio: 0.9103
- Average latency/request: 1.0 ms
- Total cost estimate: $0.003922

## Case Results

| Case | Chatbot | Agent | Agent Steps |
| :--- | :---: | :---: | ---: |
| exam_room_1 | PASS | PASS | 3 |
| exam_room_2 | PASS | PASS | 3 |
| exam_room_3 | PASS | PASS | 3 |
| student_list_subject | PASS | PASS | 2 |
| student_list_range | PASS | PASS | 2 |
| student_profile | PASS | PASS | 2 |

## Sample Outputs

### Case 1: exam_room_1
- Query: Cho minh lich thi mon Big Data cua MSSV 1 va phong thi o dau?
- Expected terms: thi luc, phong, toa
- Chatbot: Mon Big Data thi luc 11:00:00 ngay 2026-06-03 tai phong D401. Phong D401 thuoc toa D, tang 4.
- Agent: Mon Big Data thi luc 11:00:00 ngay 2026-06-03 tai phong D401. Phong D401 thuoc toa D, tang 4.

### Case 2: exam_room_2
- Query: Cho minh lich thi mon Học máy cua MSSV 1 va phong thi o dau?
- Expected terms: thi luc, phong, toa
- Chatbot: Mon Học máy thi luc 16:00:00 ngay 2026-06-14 tai phong B502. Phong B502 thuoc toa B, tang 5.
- Agent: Mon Học máy thi luc 16:00:00 ngay 2026-06-14 tai phong B502. Phong B502 thuoc toa B, tang 5.

### Case 3: exam_room_3
- Query: Cho minh lich thi mon Lập trình IoT cua MSSV 1 va phong thi o dau?
- Expected terms: thi luc, phong, toa
- Chatbot: Mon Lập trình IoT thi luc 12:00:00 ngay 2026-06-18 tai phong A301. Phong A301 thuoc toa A, tang 3.
- Agent: Mon Lập trình IoT thi luc 12:00:00 ngay 2026-06-18 tai phong A301. Phong A301 thuoc toa A, tang 3.

### Case 4: student_list_subject
- Query: Cho toi danh sach cac sinh vien hoc mon Hoc may
- Expected terms: 2a2026, sinhvien
- Chatbot: 2A202600001 - SinhVien 1
2A202600002 - SinhVien 2
2A202600003 - SinhVien 3
2A202600004 - SinhVien 4
2A202600005 - SinhVien 5
2A202600006 - SinhVien 6
2A202600007 - SinhVien 7
2A202600009 - SinhVien 9
2A202600010 - SinhVien 10
2A202600011 - SinhVien 11
- Agent: 2A202600001 - SinhVien 1
2A202600002 - SinhVien 2
2A202600003 - SinhVien 3
2A202600004 - SinhVien 4
2A202600005 - SinhVien 5
2A202600006 - SinhVien 6
2A202600007 - SinhVien 7
2A202600009 - SinhVien 9
2A202600010 - SinhVien 10
2A202600011 - SinhVien 11

### Case 5: student_list_range
- Query: Cho toi danh sach sinh vien tu 101 den 105
- Expected terms: 2a202600101, 2a202600105
- Chatbot: 2A202600101 - SinhVien 101
2A202600102 - SinhVien 102
2A202600103 - SinhVien 103
2A202600104 - SinhVien 104
2A202600105 - SinhVien 105
- Agent: 2A202600101 - SinhVien 101
2A202600102 - SinhVien 102
2A202600103 - SinhVien 103
2A202600104 - SinhVien 104
2A202600105 - SinhVien 105

### Case 6: student_profile
- Query: Thong tin sinh vien 2A202600632
- Expected terms: sinhvien 632, 2a202600632
- Chatbot: Sinh vien: SinhVien 632 (MSSV: 2A202600632)
- Agent: Sinh vien: SinhVien 632 (MSSV: 2A202600632)
