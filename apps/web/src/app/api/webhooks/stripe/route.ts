import { NextRequest, NextResponse } from "next/server";
import Stripe from "stripe";
import { getAdminDb } from "@/lib/firebase-admin";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET!;

// Price IDs for plan identification
const PRICE_IDS = {
  PRO_MONTHLY: process.env.STRIPE_PRICE_PRO_MONTHLY!,
  PRO_YEARLY: process.env.STRIPE_PRICE_PRO_YEARLY!,
  PREMIUM_MONTHLY: process.env.STRIPE_PRICE_PREMIUM_MONTHLY!,
} as const;

type SubscriptionPlan = "free" | "pro" | "premium";
type SubscriptionStatus = "active" | "past_due" | "canceled" | "incomplete";

interface SubscriptionData {
  plan: SubscriptionPlan;
  status: SubscriptionStatus;
  stripeCustomerId: string;
  stripeSubscriptionId?: string;
  currentPeriodEnd?: Date;
  updatedAt: Date;
}

/**
 * Determine subscription plan from Stripe price ID
 */
function getPlanFromPriceId(priceId: string): SubscriptionPlan {
  switch (priceId) {
    case PRICE_IDS.PRO_MONTHLY:
    case PRICE_IDS.PRO_YEARLY:
      return "pro";
    case PRICE_IDS.PREMIUM_MONTHLY:
      return "premium";
    default:
      console.warn(`Unknown price ID: ${priceId}, defaulting to free`);
      return "free";
  }
}

/**
 * Find user document by Stripe customer ID
 */
async function findUserByCustomerId(
  customerId: string
): Promise<string | null> {
  const db = getAdminDb();
  const usersRef = db.collection("users");

  const snapshot = await usersRef
    .where("subscription.stripeCustomerId", "==", customerId)
    .limit(1)
    .get();

  if (snapshot.empty) {
    return null;
  }

  return snapshot.docs[0].id;
}

/**
 * Update user subscription in Firestore
 */
async function updateUserSubscription(
  userId: string,
  subscriptionData: Partial<SubscriptionData>
): Promise<void> {
  const db = getAdminDb();
  const userRef = db.collection("users").doc(userId);

  await userRef.update({
    subscription: {
      ...subscriptionData,
      updatedAt: new Date(),
    },
  });

  console.log(`Updated subscription for user ${userId}:`, subscriptionData);
}

/**
 * Handle checkout.session.completed event
 * User completed payment - activate subscription
 */
async function handleCheckoutCompleted(
  session: Stripe.Checkout.Session
): Promise<void> {
  const userId = session.metadata?.userId;

  if (!userId) {
    throw new Error("No userId in checkout session metadata");
  }

  if (!session.customer || !session.subscription) {
    throw new Error("Missing customer or subscription in checkout session");
  }

  // Fetch the subscription to get price details
  const subscription = await stripe.subscriptions.retrieve(
    session.subscription as string
  ) as unknown as Stripe.Subscription;

  const priceId = subscription.items.data[0]?.price.id;
  if (!priceId) {
    throw new Error("No price ID found in subscription");
  }

  const plan = getPlanFromPriceId(priceId);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const periodEnd = (subscription as any).current_period_end as number | undefined;

  await updateUserSubscription(userId, {
    plan,
    status: "active",
    stripeCustomerId: session.customer as string,
    stripeSubscriptionId: session.subscription as string,
    currentPeriodEnd: periodEnd ? new Date(periodEnd * 1000) : undefined,
  });
}

/**
 * Handle customer.subscription.updated event
 * Subscription was renewed, plan changed, or status updated
 */
async function handleSubscriptionUpdated(
  subscription: Stripe.Subscription
): Promise<void> {
  const customerId = subscription.customer as string;
  const userId = await findUserByCustomerId(customerId);

  if (!userId) {
    console.warn(`No user found for customer ${customerId}`);
    return;
  }

  const priceId = subscription.items.data[0]?.price.id;
  if (!priceId) {
    throw new Error("No price ID found in subscription");
  }

  const plan = getPlanFromPriceId(priceId);
  const status = subscription.status as SubscriptionStatus;

  await updateUserSubscription(userId, {
    plan,
    status,
    stripeCustomerId: customerId,
    stripeSubscriptionId: subscription.id,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    currentPeriodEnd: (subscription as any).current_period_end
      ? new Date(((subscription as any).current_period_end as number) * 1000)
      : undefined,
  });
}

/**
 * Handle customer.subscription.deleted event
 * Subscription was cancelled - revert to free plan
 */
async function handleSubscriptionDeleted(
  subscription: Stripe.Subscription
): Promise<void> {
  const customerId = subscription.customer as string;
  const userId = await findUserByCustomerId(customerId);

  if (!userId) {
    console.warn(`No user found for customer ${customerId}`);
    return;
  }

  await updateUserSubscription(userId, {
    plan: "free",
    status: "canceled",
    stripeCustomerId: customerId,
    stripeSubscriptionId: subscription.id,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    currentPeriodEnd: (subscription as any).current_period_end
      ? new Date(((subscription as any).current_period_end as number) * 1000)
      : undefined,
  });
}

/**
 * Handle invoice.payment_failed event
 * Payment failed - mark subscription as past_due
 */
async function handlePaymentFailed(invoice: Stripe.Invoice): Promise<void> {
  const customerId = invoice.customer as string;
  const userId = await findUserByCustomerId(customerId);

  if (!userId) {
    console.warn(`No user found for customer ${customerId}`);
    return;
  }

  const db = getAdminDb();
  const userRef = db.collection("users").doc(userId);

  await userRef.update({
    "subscription.status": "past_due",
    "subscription.updatedAt": new Date(),
  });

  console.log(`Marked user ${userId} subscription as past_due`);
}

/**
 * POST /api/webhooks/stripe
 * Stripe webhook endpoint
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.text();
    const signature = request.headers.get("stripe-signature");

    if (!signature) {
      console.error("Missing stripe-signature header");
      return NextResponse.json(
        { error: "Missing signature" },
        { status: 400 }
      );
    }

    // Verify webhook signature
    let event: Stripe.Event;
    try {
      event = stripe.webhooks.constructEvent(body, signature, webhookSecret);
    } catch (err) {
      console.error(
        "Webhook signature verification failed:",
        err instanceof Error ? err.message : "Unknown error"
      );
      return NextResponse.json(
        { error: "Invalid signature" },
        { status: 400 }
      );
    }

    // Handle the event
    console.log(`Processing webhook event: ${event.type}`);

    try {
      switch (event.type) {
        case "checkout.session.completed":
          await handleCheckoutCompleted(
            event.data.object as Stripe.Checkout.Session
          );
          break;

        case "customer.subscription.updated":
          await handleSubscriptionUpdated(
            event.data.object as Stripe.Subscription
          );
          break;

        case "customer.subscription.deleted":
          await handleSubscriptionDeleted(
            event.data.object as Stripe.Subscription
          );
          break;

        case "invoice.payment_failed":
          await handlePaymentFailed(event.data.object as Stripe.Invoice);
          break;

        default:
          console.log(`Unhandled event type: ${event.type}`);
      }
    } catch (err) {
      // Log the error but return 200 to Stripe to prevent retries
      // Stripe will retry failed webhooks automatically
      console.error(
        `Error processing webhook ${event.type}:`,
        err instanceof Error ? err.message : "Unknown error"
      );
      console.error("Event data:", JSON.stringify(event.data.object, null, 2));

      // Still return 200 to acknowledge receipt
      return NextResponse.json({
        received: true,
        error: err instanceof Error ? err.message : "Unknown error",
      });
    }

    return NextResponse.json({ received: true });
  } catch (err) {
    console.error("Webhook handler error:", err);
    return NextResponse.json(
      {
        error: "Internal server error",
        message: err instanceof Error ? err.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}
