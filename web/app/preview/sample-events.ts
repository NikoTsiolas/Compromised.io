// SAMPLE DATA. Invented events that exist only to show the design with every field filled in.
// None of these incidents happened. Organisations are fictional (Microsoft's sample company
// names), publishers are placeholders, links go to example.com, and CVE numbers use the
// impossible year 0000 so they can never match a real identifier. Trust labels use only wording
// the API's verifier can produce (api/src/compromised/pipeline/verifier.py).
// Imported only by app/preview/page.preview.tsx, which production builds do not include.
import type { FeedItem } from "@/lib/feed";

/** The fixed "now" the sample is drawn against, so relative times never drift. */
export const SAMPLE_NOW = new Date("2026-11-26T15:00:00Z");

const source = (
  publisher: string,
  slug: string,
  headline: string,
  publishedAt: string,
) => ({
  publisher,
  url: `https://example.com/sample/${slug}`,
  headline,
  publishedAt,
});

export const SAMPLE_ITEMS: FeedItem[] = [
  {
    id: "sample-1",
    live: true,
    headline: "Fabrikam warns attackers are exploiting a flaw in its home routers",
    url: "https://example.com/sample/fabrikam-router-advisory",
    publisher: "Fabrikam security advisory",
    publishedAt: "2026-11-26T14:32:00Z",
    organization: "Fabrikam home routers",
    category: "exploited_vulnerability",
    summary:
      "Attackers are taking over some Fabrikam home routers through a weakness in their settings page. Fabrikam has released a fix.",
    actionLine: "Update your Fabrikam router's software now.",
    trust: {
      status: "confirmed",
      label: "Flaw confirmed by the company",
      score: 100,
      sources: ["Fabrikam security advisory", "Example Wire", "Sample Times"],
    },
    cves: ["CVE-0000-00001"],
    attackVector: "Over the internet, through the router's web settings page",
    sources: [
      source(
        "Fabrikam security advisory",
        "fabrikam-router-advisory",
        "Security update for Fabrikam home routers",
        "2026-11-26T14:32:00Z",
      ),
      source(
        "Example Wire",
        "fabrikam-routers-exploited",
        "Fabrikam warns attackers are exploiting a flaw in its home routers",
        "2026-11-26T14:41:00Z",
      ),
      source(
        "Sample Times",
        "fabrikam-patch",
        "Router owners urged to patch after Fabrikam flaw comes under attack",
        "2026-11-26T14:55:00Z",
      ),
    ],
  },
  {
    id: "sample-2",
    headline:
      "Northwind Pharmacy says customer names and prescriptions were exposed in breach",
    url: "https://example.com/sample/northwind-breach",
    publisher: "Example Wire",
    publishedAt: "2026-11-26T13:05:00Z",
    organization: "Northwind Pharmacy",
    category: "breach",
    summary:
      "An outsider got into Northwind Pharmacy's online ordering system and copied customer names, addresses and prescription histories. Payment cards were not affected, the company says.",
    trust: {
      status: "reported",
      label: "Reported by 3 news outlets",
      score: 70,
      sources: ["Example Wire", "Sample Times", "Placeholder Post"],
    },
    cves: [],
    attackVector: "Stolen staff password",
    sources: [
      source(
        "Example Wire",
        "northwind-breach",
        "Northwind Pharmacy says customer names and prescriptions were exposed in breach",
        "2026-11-26T13:05:00Z",
      ),
      source(
        "Sample Times",
        "northwind-customers",
        "Northwind customers told to watch for scam calls after data theft",
        "2026-11-26T13:40:00Z",
      ),
      source(
        "Placeholder Post",
        "northwind-ordering",
        "Pharmacy chain Northwind confirms ordering system intrusion",
        "2026-11-26T14:10:00Z",
      ),
    ],
  },
  {
    id: "sample-3",
    headline: "Ransomware group claims attack on Tailspin Logistics",
    url: "https://example.com/sample/tailspin-claim",
    publisher: "Sample Claims Tracker",
    publishedAt: "2026-11-26T11:40:00Z",
    organization: "Tailspin Logistics",
    category: "ransomware",
    // Present on purpose: attacker claims never show a photo, so every page must draw the tile.
    image: { url: "https://images.example.com/sample/claim-screenshot.png", publisher: "Sample Claims Tracker" },
    summary:
      "A criminal group says it stole files from Tailspin Logistics. No company, government or news outlet has confirmed this yet.",
    trust: {
      status: "claimed",
      label: "Claimed by attackers, not confirmed",
      score: 20,
      sources: ["Sample Claims Tracker"],
    },
    cves: [],
    attackVector: null,
    sources: [
      source(
        "Sample Claims Tracker",
        "tailspin-claim",
        "Tailspin Logistics listed by ransomware group",
        "2026-11-26T11:40:00Z",
      ),
    ],
  },
  {
    id: "sample-4",
    headline: "Woodgrove Hospital diverts ambulances after IT systems go down",
    url: "https://example.com/sample/woodgrove-outage",
    publisher: "Placeholder Post",
    publishedAt: "2026-11-26T10:15:00Z",
    organization: "Woodgrove Hospital",
    category: "ransomware",
    summary:
      "Woodgrove Hospital is sending ambulances elsewhere while its computer systems are down. The hospital says it is investigating the cause.",
    // "Under investigation" is set by no rule yet (wiki, trust labels as built), so a
    // hospital's own "investigating" wording still reads as one outlet's report.
    trust: {
      status: "reported",
      label: "Reported by 1 news outlet",
      score: 50,
      sources: ["Placeholder Post"],
    },
    cves: [],
    attackVector: null,
    sources: [
      source(
        "Placeholder Post",
        "woodgrove-outage",
        "Woodgrove Hospital diverts ambulances after IT systems go down",
        "2026-11-26T10:15:00Z",
      ),
    ],
  },
  {
    id: "sample-5",
    headline: "Adatum Messaging denies report that user chats were leaked",
    url: "https://example.com/sample/adatum-disputed",
    publisher: "Sample Times",
    publishedAt: "2026-11-26T09:02:00Z",
    organization: "Adatum Messaging",
    category: "breach",
    summary:
      "A report said private chats from Adatum Messaging were posted online. Adatum says the files are old test data and no user chats were exposed.",
    trust: {
      status: "disputed",
      label: "Disputed",
      score: 10,
      sources: ["Example Wire", "Sample Times"],
    },
    cves: [],
    attackVector: null,
    sources: [
      source(
        "Example Wire",
        "adatum-leak",
        "Adatum Messaging chats appear on leak forum, researcher says",
        "2026-11-25T21:30:00Z",
      ),
      source(
        "Sample Times",
        "adatum-disputed",
        "Adatum Messaging denies report that user chats were leaked",
        "2026-11-26T09:02:00Z",
      ),
    ],
  },
  {
    id: "sample-6",
    headline: "Litware releases urgent update for Office Suite after critical flaw",
    url: "https://example.com/sample/litware-update",
    publisher: "Litware security advisory",
    publishedAt: "2026-11-25T18:20:00Z",
    organization: "Litware Office Suite",
    category: "vulnerability",
    summary:
      "Opening a booby-trapped document in Litware Office Suite could let an attacker take over the computer. Litware has fixed it.",
    actionLine: "Install the November update for Litware Office Suite.",
    trust: {
      status: "confirmed",
      label: "Flaw confirmed by the company",
      score: 90,
      sources: ["Litware security advisory"],
    },
    cves: ["CVE-0000-00002", "CVE-0000-00003"],
    attackVector: "Opening a malicious document",
    sources: [
      source(
        "Litware security advisory",
        "litware-update",
        "November security update for Litware Office Suite",
        "2026-11-25T18:20:00Z",
      ),
    ],
  },
  {
    id: "sample-7",
    headline: "Researchers detail phishing kit that copies bank login pages",
    url: "https://example.com/sample/phishing-kit",
    publisher: "Example Wire",
    publishedAt: "2026-11-25T16:45:00Z",
    organization: null,
    category: "research",
    summary:
      "Security researchers describe a tool criminals use to make convincing fake bank login pages. It is sold online and has been seen in several countries.",
    trust: {
      status: "reported",
      label: "Reported by 1 news outlet",
      score: 50,
      sources: ["Example Wire"],
    },
    cves: [],
    attackVector: "Fake login pages sent by text message",
    sources: [
      source(
        "Example Wire",
        "phishing-kit",
        "Researchers detail phishing kit that copies bank login pages",
        "2026-11-25T16:45:00Z",
      ),
    ],
  },
];

/** The tab list the API serves (GET /v1/tabs), so the preview needs no API. */
export const SAMPLE_TABS = [
  { id: "all", label: "All" },
  { id: "breaches", label: "Breaches" },
  { id: "ransomware", label: "Ransomware" },
  { id: "under-attack", label: "Under attack" },
  { id: "update-now", label: "Update now" },
  { id: "research", label: "Research" },
  { id: "trending", label: "Trending" },
];
