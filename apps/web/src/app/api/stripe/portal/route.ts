import { NextRequest, NextResponse } from "next/server";
import Stripe from "stripe";

// Lazy init — avoid module-level env access during Next.js build
function getStripe() {
  return new Stripe(process.env.STRIPE_SECRET_KEY!);
}

/**
 * POST /api/stripe/portal
 * Creates a Stripe Customer Portal session for subscription management
 */
export async function POST(req: NextRequest) {
  try {
    const { customerId, locale } = await req.json();

    if (!customerId) {
      return NextResponse.json(
        { error: "Missing customerId" },
        { status: 400 }
      );
    }

    const session = await getStripe().billingPortal.sessions.create({
      customer: customerId,
      return_url: `${req.nextUrl.origin}/${locale || "en"}/dashboard`,
    });

    return NextResponse.json({ url: session.url });
  } catch (error) {
    console.error("Error creating portal session:", error);
    return NextResponse.json(
      {
        error:
          error instanceof Error
            ? error.message
            : "Failed to create portal session",
      },
      { status: 500 }
    );
  }
}
