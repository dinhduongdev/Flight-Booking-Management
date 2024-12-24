from flask import redirect, flash, render_template, url_for, request
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask_admin import AdminIndexView, BaseView, Admin, expose
from datetime import datetime as dt

from app import app, db
from app.blueprints.auth.models import User
from app.blueprints.auth.models import UserRole
from app.blueprints.auth.routes import logout_process
from app.blueprints.flights.models import *
from app.blueprints.flights import dao as flight_dao
from app.blueprints.bookings.models import Payment, Reservation


class AuthenticatedView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated


class AdminView(AuthenticatedView):
    def is_accessible(self):
        return super().is_accessible() and current_user.role == UserRole.ADMIN


class DashboardAdmin(AdminIndexView, AdminView):
    @expose("/", methods=["GET", "POST"])
    def index(self):
        year = request.args.get('year', type=int, default=2024)  
        month = request.args.get('month', type=int, default=12)  
        flight_stats = flight_dao.get_flight_count_by_route(year, month)
        
        return self.render('admin/dashboard.html', stats=flight_stats, year=year, month=month)

class CountryAdmin(ModelView, AdminView):
    column_list = ("id", "name", "code")
    form_excluded_columns = ["airports"]
    column_searchable_list = ["name", "code"]

    def create_model(self, form):
        if flight_dao.get_country_by_code(form.code.data):
            form.code.errors.append("Country code already exists!")
            return False
        return super().create_model(form)

    def update_model(self, form, model):
        updated_country = flight_dao.get_country_by_code(form.code.data)
        if updated_country and updated_country.id != model.id:
            form.code.errors.append("Country code already exists!")
            return False
        return super().update_model(form, model)


class UserView(ModelView, AdminView):
    column_list = (
        "id",
        "first_name",
        "last_name",
        "email",
        "citizen_id",
        "phone",
        "role",
    )
    column_searchable_list = ["first_name", "last_name", "email", "citizen_id", "phone"]


class RouteAdmin(ModelView, AdminView):
    column_list = [
        "id",
        "depart_airport.name",
        "depart_airport.id",
        "arrive_airport.name",
        "arrive_airport.id",
    ]
    form_excluded_columns = ["flights"]
    column_searchable_list = ["depart_airport.name"]

    def create_model(self, form):
        route = flight_dao.get_route_by_airports(
            form.depart_airport.data.id, form.arrive_airport.data.id
        )
        if route:
            flash(f"Route already exists! {route}", "danger")
            return False
        return super().create_model(form)

    def update_model(self, form, model):
        existed_route = flight_dao.get_route_by_airports(
            form.depart_airport.data.id, form.arrive_airport.data.id
        )
        if existed_route and existed_route.id != model.id:
            flash(f"Route already exists! {existed_route}", "danger")
            return False
        return super().update_model(form, model)


class FlightAdmin(ModelView, AdminView):
    column_list = (
        "id",
        "route.depart_airport.name",
        "route.arrive_airport.name",
        "depart_time",
        "arrive_time",
        "aircraft.id",
        "aircraft.name",
        "aircraft.airline.name",
    )
    column_labels = {
        "route.depart_airport.name": "Depart Airport",
        "route.arrive_airport.name": "Arrive Airport",
        "aircraft.id": "Aircraft ID",
        "aircraft.name": "Aircraft Name",
        "aircraft.airline.name": "Airline Name",
    }
    column_searchable_list = [
        "id",
        "route.depart_airport.name",
        "route.arrive_airport.name",
    ]

    form_excluded_columns = ["flight_seats"]

    def create_model(self, form):
        # Check depart_time < arrive_time
        if form.depart_time.data >= form.arrive_time.data:
            form.depart_time.errors.append("Depart time must be before arrive time!")
            form.arrive_time.errors.append("Depart time must be before arrive time!")
            return False
        # Check if aircraft is not available
        if not form.aircraft.data.is_available(
            form.depart_time.data, form.arrive_time.data
        ):
            form.aircraft.errors.append("Aircraft is not available at this time!")
            return False
        # Create seats for flight
        return super().create_model(form)

    # def update_model(self, form, model):
    #     new_arrive_time = form.arrive_time.data
    #     new_aircraft = flight_dao.get_aircraft_by_id(form.aircraft.data.id)

    #     return False
    #     # return super().update_model(form, model)

    @expose("/new", methods=["GET"])
    def create_view(self):
        return redirect(url_for("flights.show_routes"))


class AirportAdmin(ModelView, AdminView):
    column_list = ("id", "name", "code", "country")
    form_excluded_columns = ["stopovers", "depart_routes", "arrive_routes"]
    column_searchable_list = ["code", "name", "country.name"]
    column_filters = ["country.name"]
    column_sortable_list = ["id", "name", "code", "country.name"]

    def create_model(self, form):
        if flight_dao.get_airport_by_code(form.code.data):
            form.code.errors.append("Airport code already exists!")
            return False
        return super().create_model(form)

    def update_model(self, form, model):
        updated_airport = flight_dao.get_airport_by_code(form.code.data)
        if updated_airport and updated_airport.id != model.id:
            form.code.errors.append("Country code already exists!")
            return False
        return super().update_model(form, model)


class AircraftAdmin(ModelView, AdminView):
    # Hiển thị thêm airline.name
    column_list = ("id", "name", "airline.name")
    form_excluded_columns = ["flights"]
    column_searchable_list = [
        "id",
        "name",
        "airline.name",
    ]
    column_sortable_list = ["id", "name", "airline.name"]

    @expose("/new", methods=("GET", "POST"))
    def create_view(self):
        if request.method == "POST":
            airline_id = request.form.get("airline_id")
            aircraft_name = request.form.get("aircraft_name")
            seat_data = {}
            for name, value in request.form.items():
                if name.startswith("class") and value:
                    class_id = int(name.replace("class", ""))
                    seat_data[class_id] = int(value)

            # Validate data
            if not seat_data:
                flash("Please input seat data!", "danger")
                return self.render("admin/createAirCraft.html")

            # Add aircraft
            try:
                flight_dao.add_aircraft(aircraft_name, airline_id, seat_data)
            except Exception as e:
                db.session.rollback()
                flash(f"Error: {e}", "danger")
                return self.render("admin/createAirCraft.html")

            flash("Create aircraft successfully!", "success")
            return redirect(url_for("aircraft.index_view"))
        return self.render("admin/createAirCraft.html")


class AirlineAdmin(ModelView, AdminView):
    column_list = ("id", "name")
    column_searchable_list = ["id", "name"]
    form_excluded_columns = ["aircrafts"]


class SeatClassAdmin(ModelView, AdminView):
    form_excluded_columns = ["seats"]


class AircraftSeatAdmin(ModelView, AdminView):
    column_list = ("id", "aircraft", "seat_class", "seat_name")
    form_excluded_columns = ["flight_seats"]


class FlightSeatAdmin(ModelView, AdminView):
    column_list = ("flight.id", "aircraft_seat", "price", "currency")
    column_searchable_list = ["flight.id"]


class RegulationView(ModelView, AdminView):
    form_excluded_columns = ["key"]
    can_create = False
    can_delete = False


class ReservationView(ModelView, AdminView):
    column_list = ("id", "owner", "author", "flight_seat", "payment")


class PaymentView(ModelView, AdminView):
    column_list = (
        "id",
        "reservation_id",
        "amount",
        "status",
        "created_at",
    )


class LogoutView(AuthenticatedView):
    @expose("/")
    def index(self):
        return logout_process()


class HomeView(AuthenticatedView):
    @expose("/")
    def index(self):
        return redirect("/")


admin = Admin(
    app,
    template_mode="bootstrap4",
    index_view=DashboardAdmin(name="Dashboard"),
)

admin.add_view(UserView(User, db.session, name="Users"))
admin.add_view(CountryAdmin(Country, db.session, name="Countries"))
admin.add_view(AirportAdmin(Airport, db.session, name="Airports"))
admin.add_view(AirlineAdmin(Airline, db.session, name="Airlines"))
admin.add_view(AircraftAdmin(Aircraft, db.session, name="Aircrafts"))
admin.add_view(AircraftSeatAdmin(AircraftSeat, db.session, name="AircraftSeats"))
admin.add_view(SeatClassAdmin(SeatClass, db.session, name="SeatClasses"))
admin.add_view(RouteAdmin(Route, db.session, name="Routes"))
admin.add_view(FlightAdmin(Flight, db.session, name="Flights"))
admin.add_view(FlightSeatAdmin(FlightSeat, db.session, name="FlightSeats"))
admin.add_view(ReservationView(Reservation, db.session, name="Reservations"))
admin.add_view(PaymentView(Payment, db.session, name="Payments"))
admin.add_view(RegulationView(Regulation, db.session, name="Regulations"))
admin.add_view(HomeView(name="Home", menu_class_name="bg-success"))
admin.add_view(LogoutView(name="Logout", menu_class_name="bg-danger"))
