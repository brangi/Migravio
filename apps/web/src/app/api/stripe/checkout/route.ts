import { NextRequest, NextResponse } from "next/server";
import Stripe from "stripe";

// Lazy init — avoid module-level env access during Next.js build
function getStripe() {
  return new Stripe(process.env.STRIPE_SECRET_KEY!);
}

/**
 * POST /api/stripe/checkout
 * Creates a Stripe Checkout Session for subscription purchase
 */
export async function POST(req: NextRequest) {
  try {
    const { priceId, locale, userId } = await req.json();

    // Validate required fields
    if (!priceId || !userId) {
      return NextResponse.json(
        { error: "Missing required fields: priceId and userId" },
        { status: 400 }
      );
    }

    const currentLocale = locale || "en";
    const origin = req.nextUrl.origin;

    // Create Stripe Checkout Session
    const session = await getStripe().checkout.sessions.create({
      mode: "subscription",
      payment_method_types: ["card"],
      line_items: [
        {
          price: priceId,
          quantity: 1,
        },
      ],
      success_url: `${origin}/${currentLocale}/dashboard?payment=success`,
      cancel_url: `${origin}/${currentLocale}/pricing?payment=cancelled`,
      metadata: {
        userId,
        locale: currentLocale,
      },
      // Allow promotion codes for discounts
      allow_promotion_codes: true,
      // Collect customer email if not already known
      customer_email: undefined, // Stripe will collect this
    });

    return NextResponse.json({ url: session.url });
  } catch (error) {
    console.error("Error creating checkout session:", error);
    return NextResponse.json(
      {
        error:
          error instanceof Error
            ? error.message
            : "Failed to create checkout session",
      },
      { status: 500 }
    );
  }
}
