app_name = "taxiye_eims_integration"
app_title = "Taxiye Eims Integration"
app_publisher = "Mevinai"
app_description = "taxiye_eims_integration"
app_email = "sintayehu@mevinai.com"
app_license = "mit"




# doc_events = {
#     "Trip Invoice": {
#         "on_submit": "taxiye_eims_integration.taxiye_eims_integration.doctype.trip_invoice.trip_invoice.on_submit"
#     },
#     "Trip Receipt": {
#         "on_submit": "taxiye_eims_integration.taxiye_eims_integration.doctype.trip_receipt.trip_receipt.on_submit"
#     }
# }




# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "taxiye_eims_integration",
# 		"logo": "/assets/taxiye_eims_integration/logo.png",
# 		"title": "Taxiye Eims Integration",
# 		"route": "/taxiye_eims_integration",
# 		"has_permission": "taxiye_eims_integration.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/taxiye_eims_integration/css/taxiye_eims_integration.css"
# app_include_js = "/assets/taxiye_eims_integration/js/taxiye_eims_integration.js"

# include js, css files in header of web template
# web_include_css = "/assets/taxiye_eims_integration/css/taxiye_eims_integration.css"
# web_include_js = "/assets/taxiye_eims_integration/js/taxiye_eims_integration.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "taxiye_eims_integration/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "taxiye_eims_integration/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "taxiye_eims_integration.utils.jinja_methods",
# 	"filters": "taxiye_eims_integration.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "taxiye_eims_integration.install.before_install"
# after_install = "taxiye_eims_integration.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "taxiye_eims_integration.uninstall.before_uninstall"
# after_uninstall = "taxiye_eims_integration.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "taxiye_eims_integration.utils.before_app_install"
# after_app_install = "taxiye_eims_integration.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "taxiye_eims_integration.utils.before_app_uninstall"
# after_app_uninstall = "taxiye_eims_integration.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "taxiye_eims_integration.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"taxiye_eims_integration.tasks.all"
# 	],
# 	"daily": [
# 		"taxiye_eims_integration.tasks.daily"
# 	],
# 	"hourly": [
# 		"taxiye_eims_integration.tasks.hourly"
# 	],
# 	"weekly": [
# 		"taxiye_eims_integration.tasks.weekly"
# 	],
# 	"monthly": [
# 		"taxiye_eims_integration.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "taxiye_eims_integration.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "taxiye_eims_integration.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "taxiye_eims_integration.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "taxiye_eims_integration.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["taxiye_eims_integration.utils.before_request"]
# after_request = ["taxiye_eims_integration.utils.after_request"]

# Job Events
# ----------
# before_job = ["taxiye_eims_integration.utils.before_job"]
# after_job = ["taxiye_eims_integration.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"taxiye_eims_integration.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

