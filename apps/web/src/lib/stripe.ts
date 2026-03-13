/**
 * Stripe client helper
 * Handles redirecting users to Stripe Checkout
 */

export async function redirectToCheckout(
  priceId: string,
  locale: string,
  userId: string
): Promise<void> {
  try {
    const res = await fetch("/api/stripe/checkout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ priceId, locale, userId }),
    });

    if (!res.ok) {
      throw new Error("Failed to create checkout session");
    }

    const { url } = await res.json();

    if (url) {
      window.location.href = url;
    } else {
      throw new Error("No checkout URL returned");
    }
  } catch (error) {
    console.error("Error redirecting to checkout:", error);
    throw error;
  }
}
