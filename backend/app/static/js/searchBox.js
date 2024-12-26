async function fetchRoutes() {
  const response = await fetch("/api/routes");
  const data = await response.json();
  return data;
}
function getArrivalAirportsByDepartureAirport(
  routes,
  departAirportID
) {
  let filteredRoutes = routes.filter((route) => route.depart_airport_id == departAirportID);
  return filteredRoutes.map((route) => route.arrive_airport_id);
}

document.addEventListener("DOMContentLoaded", function () {
  fetchRoutes().then((data) => {
    const routes = data;
    const departAirportSelect = document.getElementById("departure_airport");
    const arrivalAirportSelect = document.getElementById("arrival_airport");
    const departureDate = document.getElementById("departure_date");
    
    departAirportSelect.addEventListener("change", function () {
      let departAirportID = departAirportSelect.value;
      let arrivalAirports = getArrivalAirportsByDepartureAirport(
        routes,
        departAirportID
      );
      

    Array.from(arrivalAirportSelect.options).forEach((option) => {
      if (arrivalAirports.includes(parseInt(option.value))) {
        option.disabled = false;
      }
      else {
        option.disabled = true;
      }
    });
    $('#arrival_airport').selectpicker('refresh');
    });
    
    // Trigger the change event to populate the arrival airports
    departAirportSelect.dispatchEvent(new Event("change"));

    const urlParams = new URLSearchParams(window.location.search);
    const departAirportID = urlParams.get("departure_airport");
    const arriveAirportID = urlParams.get("arrival_airport");
    const departDate = urlParams.get("departure_date");

    if (departAirportID) {
      departAirportSelect.value = departAirportID;
      departAirportSelect.dispatchEvent(new Event("change"));
    }

    if (arriveAirportID) {
      arrivalAirportSelect.value = arriveAirportID;
      $('#arrival_airport').selectpicker('refresh');
    }

    if (departDate) {
      departureDate.value = departDate;
    }
  });
});
