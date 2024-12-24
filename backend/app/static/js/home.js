document
  .querySelector(".find button.btn")
  .addEventListener("click", function () {
    const fromValue = document.querySelector("#from").value;
    const toValue = document.querySelector("#to").value;
    const departDateInput = document.getElementById("depart").value;

    if (fromValue && toValue  && departDateInput) {
      // Chuyển hướng đến /booking kèm theo URL Parameters
      const queryParams = new URLSearchParams({
        from: fromValue,
        to: toValue,
        departDate: departDateInput,
      }).toString();
      console.log(queryParams);
      

        window.location.href = `/booking?${queryParams}`;
    } else {
      alert('Vui lòng chọn cả "From" và "To".');
    }
  });
