from datetime import datetime

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask import redirect, render_template, url_for, request, flash
from flask_dance.contrib.github import github
from flask_login import logout_user, login_required, current_user

from app import auth, utils, crud
from app.config import settings
from app.db import db_session

routes = Blueprint('routes', __name__, url_prefix='')

with open(u'data/countries.txt', 'r', encoding="ISO-8859-1") as f:
    countries = [line.strip() for line in f]

@routes.route("/")
def homepage():
    if not github.authorized:
        return render_template("index.html")
    else:
        return redirect(url_for("routes.profile"))


@routes.route("/github")
def login():
    if not github.authorized:
        return redirect(url_for("github.login"))
    else:
        return redirect(url_for("routes.profile"))


@routes.route("/onboarding", methods=["GET"])
@login_required
def onboarding():
    if current_user.onboarded:
        return redirect(url_for("routes.profile"))
    else:
        return render_template("onboarding.html", privacy_url=settings.PRIVACY_POLICY_URL)


@routes.route("/onboarding", methods=["POST"])
@login_required
def onboarding_submit():
    request_data = request.form
    user = crud.update_user_info(
        db_session,
        update_data=request_data,
        user=current_user,
    )
    user.onboarded = True
    db_session.commit()
    return redirect(url_for("routes.email_verification"))


@routes.route("/email-verification", methods=["GET"])
@login_required
@auth.onboarding_required
def email_verification():
    if current_user.email_verified:
        return redirect(url_for("routes.profile"))
    else:
        # Check for previous verification code
        if current_user.email_verification_code:
            # Check if code is expired
            if current_user.email_verification_code_expiry > datetime.now():
                return render_template(
                    "verify_code_from_email.html", email=current_user.email
                )
        utils.send_verification_email(db=db_session, user=current_user)
        return render_template("verify_code_from_email.html", email=current_user.email)


@routes.route("/email-verification/resend", methods=["POST"])
@login_required
@auth.onboarding_required
def resend_email_verification():
    utils.send_verification_email(db=db_session, user=current_user)
    flash("A new verification code has been sent to " + current_user.email, "info")
    return redirect(url_for("routes.email_verification"))


@routes.route("/email-verification", methods=["POST"])
@login_required
@auth.onboarding_required
def email_verification_submit():
    code = request.form["verification_code"]
    if code == current_user.email_verification_code:
        current_user.email_verified = True
        db_session.commit()
        utils.send_welcome_email(user=current_user)
        flash("Email verified!", "success")
        return redirect(url_for("routes.profile"))
    else:
        flash("Invalid code", "danger")
        return redirect(url_for("routes.email_verification"))


@routes.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("routes.homepage"))


@routes.route("/profile")
@login_required
@auth.onboarding_required
@auth.email_verification_required
def profile():
    return render_template("profile.html", countries=countries)


@routes.route("/profile/edit", methods=["POST"])
@login_required
@auth.onboarding_required
@auth.email_verification_required
def edit_profile():
    request_data = request.form.to_dict()
    ####################
    # These lines remove email and username from request data
    # so they cannot be used by crud.update_user_info.
    if "email" in request_data:
        del request_data["email"]
    if "username" in request_data:
        del request_data["username"]
    # While, yes, we are using 'readonly' and 'disabled' in the HTML for these entries,
    # this does not actually prevent the user from changing the HTML
    # and sending a request with new values. So...
    # DO NOT REMOVE THESE LINES!

    # TODO: Make a schema for the request data instead.
    # https://stackoverflow.com/questions/24238743/flask-decorator-to-verify-json-and-json-schema
    ####################
    
    # Substitute checkbox values with boolean values
    if "share_with_recruiters" in request_data:
        request_data["share_with_recruiters"] = True
    else:
        request_data["share_with_recruiters"] = False

    # Update user info
    user = crud.update_user_info(
        db_session,
        update_data=request_data,
        user=current_user,
    )
    db_session.commit()
    flash("Profile updated!", "success")
    return redirect(url_for("routes.profile"))


@routes.route("/profile/delete", methods=["POST"])
@login_required
@auth.onboarding_required
@auth.email_verification_required
def delete_profile():
    user = crud.get_user_by_gh_username(
        db_session,
        username=current_user.username,
    )
    uname = user.username
    logout_user()
    crud.delete_user(db_session, user)
    flash("Your account has been deleted.", "success")
    return redirect(url_for("routes.homepage"))


@routes.route("/assessments")
@login_required
@auth.onboarding_required
@auth.email_verification_required
def assessments():
    # Get query parameters
    query_params = {
        "types": request.args.get("types"),
        "languages": request.args.get("languages"),
    }
    assessments = crud.get_assessments(
        db=db_session,
        language=query_params["languages"],
        types=query_params["types"],
    )
    languages = ["All", "R", "Python", "Bash", "Nextflow", "Snakemake"]
    types = ["All", "software", "analysis"]
    # Put language first if it is in the query parameters
    if query_params["languages"] in languages:
        languages.remove(query_params["languages"])
        languages.insert(0, query_params["languages"])
    return render_template(
        "assessments.html", assessments=assessments, languages=languages, types=types
    )


@routes.route("/documentation")
@login_required
@auth.onboarding_required
@auth.email_verification_required
def documentation():
    return redirect(
        "https://brnteam.notion.site/BRN-Skill-Assessments-09882a8300e64d33925593584afb0fab"
    )


@routes.route("/settings")
@login_required
@auth.onboarding_required
@auth.email_verification_required
def user_settings():
    return render_template("settings.html")
