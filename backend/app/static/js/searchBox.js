async function fetchAirports() {
  const response = await fetch("/api/airports");
  const data = await response.json();
  return data;
}

async function fetchRoutes() {
  const response = await fetch("/api/routes");
  const data = await response.json();
  return data;
}

async function fetchCountries() {
  const response = await fetch("/api/countries");
  const data = await response.json();
  return data;
}

function getCountryByID(countries, id) {
  return countries.find((country) => country.id == id);
}

function getAirportByID(airports, id) {
  return airports.find((airport) => airport.id == id);
}

function getRoutesByDepartAirport(routes, departAirportID) {
  return routes.filter((route) => route.depart_airport_id == departAirportID);
}

function getArrivalAirports(airports, routes) {
  return routes.map((route) =>
    getAirportByID(airports, route.arrive_airport_id)
  );
}

function getArrivalAirportsByDepartureAirport(
  airports,
  routes,
  departAirportID
) {
  let filteredRoutes = getRoutesByDepartAirport(routes, departAirportID);
  return getArrivalAirports(airports, filteredRoutes);
}

document.addEventListener("DOMContentLoaded", function () {
  let departAirportSelect = document.getElementById("from");
  let arriveAirportSelect = document.getElementById("to");

  // Fetch airports, routes, countries
  let airports = fetchAirports();
  let routes = fetchRoutes();
  let countries = fetchCountries();

  // Append airports to select elements
  Promise.all([airports, countries]).then((values) => {
    let airports = values[0];
    console.log(airports);
    
    let countries = values[1];
    airports.forEach((airport) => {
      let option = document.createElement("option");
      option.value = airport.id;
      country_name = getCountryByID(countries, airport.country_id).name;
      option.text = `${airport.name} (${airport.code}) - ${country_name}`;
      departAirportSelect.appendChild(option);

      // Clone option and append to arriveAirportSelect
      let arvOption = option.cloneNode(true);
      arvOption.disabled = true;
      arvOption.hidden = true;
      arriveAirportSelect.appendChild(arvOption);
    });
  });

  // Handle change event on departAirportSelect
  departAirportSelect.addEventListener("change", async () => {
    let departAirportID = parseInt(departAirportSelect.value);
    let arriveAirports = getArrivalAirportsByDepartureAirport(
      await airports,
      await routes,
      departAirportID
    );

    // Hide all options of arriveAirportSelect that are not in arriveAirports
    arriveAirportSelect.childNodes.forEach((option) => {
      if (
        !arriveAirports.some((airport) => airport.id == option.value)
      ) {
        // If option.value is not in arriveAirports
        option.hidden = true;
        option.disabled = true;
      } else {
        option.hidden = false;
        option.disabled = false;
      }
    });

    // Reset arriveAirportSelect value if the selected value is not in arriveAirports
    if (
      !arriveAirports.some(
        (airport) => airport.id == parseInt(arriveAirportSelect.value)
      )
    ) {
      arriveAirportSelect.value = "";
    }
  });

  // Handle params from URL to set default values for departAirportSelect and arriveAirportSelect
  Promise.all([airports, routes, countries]).then(() => {
    const urlParams = new URLSearchParams(window.location.search);
    let departAirportID = urlParams.get("from");
    let arriveAirportID = urlParams.get("to");
    if (departAirportID && arriveAirportID) {
      departAirportSelect.value = departAirportID;
      arriveAirportSelect.value = arriveAirportID;
      // Trigger change event on departAirportSelect to update arriveAirportSelect
      departAirportSelect.dispatchEvent(new Event("change"));
    }
  });
});
