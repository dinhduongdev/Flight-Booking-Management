document.addEventListener("DOMContentLoaded", function () {
  let airlineSelect = document.getElementById("airline");
  fetch("/api/airlines")
    .then((response) => response.json())
    .then((data) => {
      // Populate the select dropdown with airlines data
      data.forEach((airline) => {
        let option = document.createElement("option");
        option.value = airline.id;
        option.text = airline.name;
        airlineSelect.appendChild(option);
      });
    })
    .catch((error) => console.error("Error fetching airlines data:", error));

  let seatClassDiv = document.querySelector(".seat-class");
  fetch("/api/seatclasses")
    .then((response) => response.json())
    .then((data) => {
      // Populate the select dropdown with airlines data
      data.forEach((seatclass) => {
        seatClassDiv.innerHTML += `
        <div class="form-group col-6">
            <label for="class${seatclass.id}" class="control-label">Number of ${seatclass.name} seats</label>
            <input type="number" class="form-control" id="class${seatclass.id}" min="1" name='class${seatclass.id}' />
        </div>
      `;
      });
    })
    .catch((error) => console.error("Error fetching airlines data:", error));
});
