document.addEventListener("DOMContentLoaded", function () {
  // Hàm định dạng thời gian ISO thành giờ phút
  function formatTime(isoTime) {
    const timeObj = new Date(isoTime);
    const hours = timeObj.getHours().toString().padStart(2, "0");
    const minutes = timeObj.getMinutes().toString().padStart(2, "0");
    return `${hours}:${minutes}`;
  }

  // Hàm render kết quả chuyến bay
  function renderFlights(container, data) {
    let i = 0;
    container.innerHTML = ""; // Xóa nội dung cũ

    if (data.success) {
        data.flights.forEach((item) => {
            // Kiểm tra sân bay trung gian
            //console.log(data.intermediate_airport[i++].length);
            
            const intermediateHTML = data.intermediate_airport[i++].length > 0
                ? `<span>TrungGian ${i}</span>`
                : `<span>Bay thẳng</span>`;

            // Thêm nội dung vào container
            container.innerHTML += `
                <div class="card rounded-pill px-5 py-10 m-5 shadow-sm">
                    <div class="row g-0">
                        <div class="col-md-4 text-center p-3">
                            <div class="w-100 h-100 d-flex align-items-center justify-content-around">
                                <div class="d-flex flex-column align-items-center">
                                    <h5>${formatTime(item.depart_time)}</h5>
                                    <p class="mb-0">${data.route.depart_airport}</p>
                                    <small>Nhà ga 1</small>
                                </div>
                                <div class="d-flex flex-column align-items-center">
                                    ${intermediateHTML}
                                    <div class="dotted-underline"></div>
                                </div>
                                <div class="d-flex flex-column align-items-center">
                                    <h5>${formatTime(item.arrive_time)}</h5>
                                    <p class="mb-0">${data.route.arrive_airport}</p>
                                    <small>Nhà ga 1</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-5 border-start border-end p-3">
                            <div class="w-100 h-100 d-flex flex-column align-items-center justify-content-center">
                                <div class="d-flex align-items-center">
                                    <i class="bi bi-clock me-2"></i>
                                    <span>Thời gian bay 2h 5 phút</span>
                                </div>
                                <div class="d-flex align-items-center mt-2">
                                    <i class="bi bi-airplane me-2"></i>
                                    <span>VN 224 Khai thác bởi Vietnam Airlines</span>
                                </div>
                                <a href="#" class="text-decoration-none mt-2 d-block">Chi tiết hành trình</a>
                            </div>
                        </div>
                        <div class="col-md-3 p-3 text-center">
                            <div class="mb-3">
                                <button class="btn btn-secondary w-100" disabled>PHỔ THÔNG <br> HẾT VÉ</button>
                            </div>
                            <div class="bg-warning rounded">
                                <span class="fw-bold">THƯƠNG GIA</span>
                                <div class="mt-2">
                                    <span class="fs-4">từ 5.860.000</span> <small>VND</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>`;
        });
    } else {
        alert(`Không tìm thấy tuyến đường. Lý do: ${data.message}`);
    }
}


  // Hàm gửi yêu cầu tìm tuyến đường
  function findRoute(fromValue, toValue, departDate) {
    const container = document.querySelector(".result-flights");
    fetch("/find_route", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          from: parseInt(fromValue, 10),
          to: parseInt(toValue, 10),
          departDate: departDate,
        }),
      })
      .then((response) => response.json())
      .then((data) => {
        console.log(data);
        
        renderFlights(container, data)
      })
      .catch((error) => console.error("Lỗi khi gửi yêu cầu:", error));
  }

  // Lấy dữ liệu từ URL và gửi yêu cầu tra cứu ban đầu
  const params = new URLSearchParams(window.location.search);
  const fromValue = params.get("from");
  const toValue = params.get("to");
  const departDate = params.get("departDate");

  if (fromValue && toValue && departDate) {
    findRoute(fromValue, toValue, departDate);
  }

  // Xử lý khi người dùng thực hiện tra cứu mới
  document.querySelector(".find button.btn").addEventListener("click", function () {
    const fromValue = document.querySelector("#from").value;
    const toValue = document.querySelector("#to").value;
    const departDateInput = document.getElementById("depart").value;

    if (fromValue && toValue) {
      // Cập nhật URL với tham số mới
      const queryParams = new URLSearchParams({
        from: fromValue,
        to: toValue,
        departDate: departDateInput,
      }).toString();
      window.history.pushState({}, "", `/booking?${queryParams}`);

      // Gửi yêu cầu mới
      findRoute(fromValue, toValue, departDateInput);
    } else {
      alert('Vui lòng chọn cả "From" và "To".');
    }
  });
});


document.getElementById("economyBtn").addEventListener("click", function() {
  // Ẩn nút "PHỔ THÔNG"
  this.style.display = "none";
  
  // Hiển thị thông tin vé "THƯƠNG GIA"
  document.getElementById("businessInfo").style.display = "block";
});
