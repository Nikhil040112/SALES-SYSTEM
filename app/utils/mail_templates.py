from datetime import datetime


def followup_reminder(user_name: str, client_name: str, follow_time: str):
    """
    Pre-overdue follow-up reminder email
    """
    return f"""
    <div style="font-family:Arial,Helvetica,sans-serif;line-height:1.6;">
        <h2 style="color:#1f2937;">Upcoming Follow-up Reminder</h2>

        <p>Hi <b>{user_name}</b>,</p>

        <p>You have a follow-up scheduled soon. Please ensure it is completed before it becomes overdue.</p>

        <table style="border-collapse:collapse;">
            <tr>
                <td style="padding:6px 12px;"><b>Client</b></td>
                <td style="padding:6px 12px;">{client_name}</td>
            </tr>
            <tr>
                <td style="padding:6px 12px;"><b>Scheduled Time</b></td>
                <td style="padding:6px 12px;">{follow_time}</td>
            </tr>
        </table>

        <p style="margin-top:16px;">
            — <br/>
            <b>Sales Pro System</b>
        </p>
    </div>
    """


def daily_summary(user_name: str, leads: list, followups: list):
    """
    Daily 8 PM summary email
    """

    lead_items = "".join(
        f"<li>{l.client_name} ({l.query_source or 'Unknown'})</li>"
        for l in leads
    ) or "<li>No pending leads 🎉</li>"

    followup_items = "".join(
        f"<li>{f['client']} — {f['time']}</li>"
        for f in followups
    ) or "<li>No pending follow-ups 🎉</li>"

    today = datetime.now().strftime("%d %b %Y")

    return f"""
    <div style="font-family:Arial,Helvetica,sans-serif;line-height:1.6;">
        <h2 style="color:#1f2937;">Daily Sales Summary</h2>

        <p>Hi <b>{user_name}</b>,</p>

        <p>Here is your pending work summary for <b>{today}</b>:</p>

        <h3>📌 Pending Leads</h3>
        <ul>
            {lead_items}
        </ul>

        <h3>⏰ Pending / Overdue Follow-ups</h3>
        <ul>
            {followup_items}
        </ul>

        <p style="margin-top:16px;">
            — <br/>
            <b>Sales Pro System</b>
        </p>
    </div>
    """