import { NextRequest, NextResponse } from "next/server";
import { Resend } from "resend";
import { getAdminDb, verifyIdToken } from "@/lib/firebase-admin";

function getResend() {
  return new Resend(process.env.RESEND_API_KEY);
}

interface ReferralRequestBody {
  attorneyId: string;
  attorneyName: string;
  attorneyEmail: string;
  userVisaType: string;
  context?: string;
}

interface UserData {
  email: string;
  firstName?: string;
  lastName?: string;
  visaType?: string;
}

interface ReferralData {
  userId: string;
  attorneyId: string;
  attorneyName: string;
  attorneyEmail: string;
  userEmail: string;
  userName: string;
  userVisaType: string;
  context?: string;
  status: "pending" | "accepted" | "declined";
  createdAt: Date;
  emailsSent: boolean;
}

/**
 * Generate email HTML for attorney introduction
 */
function generateAttorneyEmail(
  userName: string,
  userEmail: string,
  visaType: string,
  context?: string
): string {
  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>New Client Introduction from Migravio</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
  <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 8px 8px 0 0; text-align: center;">
    <h1 style="color: white; margin: 0; font-size: 24px;">New Client Introduction</h1>
  </div>

  <div style="background: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
    <p style="font-size: 16px; margin-bottom: 20px;">Hello,</p>

    <p style="font-size: 16px; margin-bottom: 20px;">
      You have received a new client referral through <strong>Migravio</strong>.
      A prospective client is seeking legal assistance with their immigration matter.
    </p>

    <div style="background: #f9fafb; border-left: 4px solid #667eea; padding: 20px; margin: 25px 0; border-radius: 4px;">
      <h2 style="margin-top: 0; font-size: 18px; color: #667eea;">Client Information</h2>
      <p style="margin: 8px 0;"><strong>Name:</strong> ${userName}</p>
      <p style="margin: 8px 0;"><strong>Email:</strong> <a href="mailto:${userEmail}" style="color: #667eea; text-decoration: none;">${userEmail}</a></p>
      <p style="margin: 8px 0;"><strong>Visa Type:</strong> ${visaType}</p>
      ${
        context
          ? `<p style="margin: 8px 0;"><strong>Message:</strong></p><p style="margin: 8px 0; padding: 15px; background: white; border-radius: 4px; border: 1px solid #e5e7eb;">${context}</p>`
          : ""
      }
    </div>

    <p style="font-size: 16px; margin-bottom: 20px;">
      The client is expecting to hear from you within 1-2 business days.
      Please reach out to them directly to discuss their case and determine next steps.
    </p>

    <div style="text-align: center; margin: 30px 0;">
      <a href="mailto:${userEmail}?subject=Re: Your Immigration Case - Migravio Referral"
         style="display: inline-block; background: #667eea; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 16px;">
        Contact Client
      </a>
    </div>

    <p style="font-size: 14px; color: #6b7280; margin-top: 30px;">
      Thank you for partnering with Migravio to serve the immigrant community.
    </p>

    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

    <p style="font-size: 12px; color: #9ca3af; margin-bottom: 10px;">
      <strong>Migravio</strong><br>
      AI-Powered Immigration Legal Platform<br>
      <a href="https://migravio.com" style="color: #667eea; text-decoration: none;">migravio.com</a>
    </p>

    <p style="font-size: 11px; color: #9ca3af; line-height: 1.4;">
      <em>Migravio provides legal information, not legal advice. We are not a law firm.
      This referral is provided as a service to connect clients with qualified attorneys.
      All attorney-client relationships are established directly between you and the client.</em>
    </p>
  </div>
</body>
</html>
  `.trim();
}

/**
 * Generate email HTML for user confirmation
 */
function generateUserConfirmationEmail(
  userName: string,
  attorneyName: string,
  attorneySpecialty: string
): string {
  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Your Attorney Introduction is On Its Way</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
  <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 8px 8px 0 0; text-align: center;">
    <h1 style="color: white; margin: 0; font-size: 24px;">Introduction Sent!</h1>
  </div>

  <div style="background: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
    <p style="font-size: 16px; margin-bottom: 20px;">Hi ${userName},</p>

    <p style="font-size: 16px; margin-bottom: 20px;">
      Great news! We've sent your introduction to <strong>${attorneyName}</strong>,
      a qualified immigration attorney specializing in <strong>${attorneySpecialty}</strong>.
    </p>

    <div style="background: #f0fdf4; border-left: 4px solid #10b981; padding: 20px; margin: 25px 0; border-radius: 4px;">
      <h2 style="margin-top: 0; font-size: 18px; color: #059669;">What Happens Next?</h2>
      <ol style="margin: 0; padding-left: 20px;">
        <li style="margin: 8px 0;">The attorney will review your information</li>
        <li style="margin: 8px 0;">They'll reach out to you within 1-2 business days</li>
        <li style="margin: 8px 0;">You'll discuss your case and next steps directly</li>
      </ol>
    </div>

    <p style="font-size: 16px; margin-bottom: 20px;">
      While you wait, continue using Migravio to track your visa status,
      explore resources, and get answers to your immigration questions.
    </p>

    <div style="text-align: center; margin: 30px 0;">
      <a href="https://migravio.com/dashboard"
         style="display: inline-block; background: #667eea; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 16px;">
        Go to Dashboard
      </a>
    </div>

    <p style="font-size: 14px; color: #6b7280; margin-top: 30px;">
      If you don't hear back within 2 business days, please contact us at
      <a href="mailto:support@migravio.com" style="color: #667eea; text-decoration: none;">support@migravio.com</a>.
    </p>

    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

    <p style="font-size: 12px; color: #9ca3af; margin-bottom: 10px;">
      <strong>Migravio</strong><br>
      AI-Powered Immigration Legal Platform<br>
      <a href="https://migravio.com" style="color: #667eea; text-decoration: none;">migravio.com</a>
    </p>

    <p style="font-size: 11px; color: #9ca3af; line-height: 1.4;">
      <em>Migravio provides legal information, not legal advice. We are not a law firm.
      Any attorney-client relationship is established directly between you and the attorney.</em>
    </p>
  </div>
</body>
</html>
  `.trim();
}

/**
 * POST /api/referrals
 * Create an attorney referral and send introduction emails
 */
export async function POST(request: NextRequest) {
  try {
    // Verify Firebase authentication
    const authHeader = request.headers.get("authorization");
    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return NextResponse.json(
        { error: "Missing or invalid authorization header" },
        { status: 401 }
      );
    }

    const idToken = authHeader.split("Bearer ")[1];
    let decodedToken;

    try {
      decodedToken = await verifyIdToken(idToken);
    } catch (err) {
      console.error("Token verification failed:", err);
      return NextResponse.json(
        { error: "Invalid or expired token" },
        { status: 401 }
      );
    }

    const userId = decodedToken.uid;

    // Parse and validate request body
    const body: ReferralRequestBody = await request.json();

    if (
      !body.attorneyId ||
      !body.attorneyName ||
      !body.attorneyEmail ||
      !body.userVisaType
    ) {
      return NextResponse.json(
        { error: "Missing required fields" },
        { status: 400 }
      );
    }

    // Get user data from Firestore
    const db = getAdminDb();
    const userDoc = await db.collection("users").doc(userId).get();

    if (!userDoc.exists) {
      return NextResponse.json({ error: "User not found" }, { status: 404 });
    }

    const userData = userDoc.data() as UserData;
    const userName = userData.firstName && userData.lastName
      ? `${userData.firstName} ${userData.lastName}`
      : userData.email.split("@")[0]; // Fallback to email username

    // Check if a similar referral already exists (within last 24 hours)
    try {
      const recentReferralsSnapshot = await db
        .collection("referrals")
        .where("userId", "==", userId)
        .where("attorneyId", "==", body.attorneyId)
        .where(
          "createdAt",
          ">",
          new Date(Date.now() - 24 * 60 * 60 * 1000) // Last 24 hours
        )
        .limit(1)
        .get();

      if (!recentReferralsSnapshot.empty) {
        return NextResponse.json(
          {
            error:
              "You already have a recent referral to this attorney. Please wait 24 hours before requesting another introduction.",
          },
          { status: 429 }
        );
      }
    } catch (indexErr) {
      // Composite index may not exist yet — skip duplicate check
      console.warn("Duplicate referral check skipped (index may be missing):", indexErr);
    }

    // Create referral document in Firestore
    const referralData: Omit<ReferralData, "context"> & { context?: string } = {
      userId,
      attorneyId: body.attorneyId,
      attorneyName: body.attorneyName,
      attorneyEmail: body.attorneyEmail,
      userEmail: userData.email,
      userName,
      userVisaType: body.userVisaType,
      status: "pending",
      createdAt: new Date(),
      emailsSent: false,
    };
    if (body.context) {
      referralData.context = body.context;
    }

    const referralRef = await db.collection("referrals").add(referralData);

    // Send emails via Resend
    let emailsSent = false;
    const emailErrors: string[] = [];

    try {
      // Send email to attorney
      // TODO: Switch to "Migravio <hello@migravio.com>" after domain verification
      const resend = getResend();
      const fromAddress = "Migravio <onboarding@resend.dev>";
      await resend.emails.send({
        from: fromAddress,
        to: body.attorneyEmail,
        subject: `New client introduction from Migravio - ${body.userVisaType} case`,
        html: generateAttorneyEmail(
          userName,
          userData.email,
          body.userVisaType,
          body.context
        ),
      });

      // Send confirmation email to user
      await resend.emails.send({
        from: fromAddress,
        to: userData.email,
        subject: "Your attorney introduction is on its way",
        html: generateUserConfirmationEmail(
          userName,
          body.attorneyName,
          body.userVisaType // Using visa type as specialty for now
        ),
      });

      emailsSent = true;
    } catch (err) {
      console.error("Error sending referral emails:", err);
      emailErrors.push(
        err instanceof Error ? err.message : "Unknown email error"
      );
      // Continue even if emails fail - referral is still created
    }

    // Update referral with email status
    await referralRef.update({
      emailsSent,
      ...(emailErrors.length > 0 && { emailErrors }),
    });

    console.log(`Created referral ${referralRef.id} for user ${userId}`);

    return NextResponse.json(
      {
        success: true,
        referralId: referralRef.id,
        emailsSent,
        message: emailsSent
          ? "Referral created and emails sent successfully"
          : "Referral created but emails failed to send",
      },
      { status: 201 }
    );
  } catch (err) {
    console.error("Referral creation error:", err);
    return NextResponse.json(
      {
        error: "Internal server error",
        message: err instanceof Error ? err.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}
