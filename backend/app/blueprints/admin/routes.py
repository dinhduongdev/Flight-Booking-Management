from flask import render_template
from . import admin_bp

@admin_bp.route("/admin")
def admin():
    return render_template('admin/master.html')

@admin_bp.route("/admin/dashboard")
def admin_dashboard():
    return render_template('admin/dashboard.html')
@admin_bp.route("/admin/flight-routes")
def admin_flightRoutes():
    return render_template('admin/flightRouteManagement.html')

@admin_bp.route("/admin/flights")
def admin_flight():
    return render_template('admin/flightManagement.html')

@admin_bp.route("/admin/change-regulations")
def admin_changeRegulation():
    return render_template('admin/changeRegulation.html')