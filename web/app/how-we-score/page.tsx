// "How we score": the confidence formula, with every number read from the API's own constants
// (GET /v1/scoring), so the page cannot drift from the code. Deliberately bare; design is #9.
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { getScoring, type Scoring } from "@/lib/api";

export const metadata: Metadata = { title: "How we score · Compromised" };

const TIER_NAMES: Record<Scoring["sources"][number]["tier"], string> = {
  official: "Official",
  press: "News outlet",
  attacker_claim: "Attacker claim",
};

export default function HowWeScore() {
  return (
    <main>
      <p>
        <Link href="/">Compromised</Link>
      </p>
      <h1>How we score</h1>
      <p>
        Every event has a label saying who reported it and a confidence score from 0 to 100. The
        score is not a measured probability: it is a fixed formula, below. It is always shown
        with its label and the names of the sources it counted. Neither the label nor the score
        is ever set by AI.
      </p>
      <Suspense fallback={<p>Loading the scoring rules…</p>}>
        <Rules />
      </Suspense>
    </main>
  );
}

async function Rules() {
  let s: Scoring;
  try {
    s = await getScoring();
  } catch {
    return <p>The scoring rules could not be loaded.</p>;
  }
  return (
    <>
      <h2>The formula</h2>
      <p>The strongest kind of source behind an event sets its label and its score:</p>
      <ul aria-label="Formula">
        <li>Claimed by attackers, with no other coverage: {s.claim_only}.</li>
        <li>Reported by one news outlet: {s.one_outlet}.</li>
        <li>
          Each additional independent news outlet: +{s.per_extra_outlet}, up to {s.press_cap}{" "}
          without official confirmation.
        </li>
        <li>
          Confirmed by an official source (the affected company, a government agency, or a
          security company&apos;s research team): {s.official}.
        </li>
        <li>Official confirmation plus news coverage: {s.official_and_press}.</li>
        <li>Disputed or retracted by a later source: {s.disputed}.</li>
      </ul>
      <p>
        Independent means a different publisher: two articles from one outlet count once. An
        attacker&apos;s claim is upgraded only when a news outlet or an official source covers the
        same incident. &ldquo;Disputed&rdquo; is set only when a later source&apos;s headline
        explicitly says the incident was denied or retracted, or that there is no evidence of it.
      </p>

      <h2>Weights</h2>
      <p>
        Each source carries a weight. By default it is its kind&apos;s number above, and then the
        formula gives exactly those numbers. A source with a different weight scores its own weight
        as the base, and as an additional outlet adds {s.per_extra_outlet} times its weight divided
        by {s.one_outlet}. The cap of {s.press_cap} without official confirmation always holds.
      </p>
      <table>
        <thead>
          <tr>
            <th scope="col">Source</th>
            <th scope="col">Kind</th>
            <th scope="col">Weight</th>
          </tr>
        </thead>
        <tbody>
          {s.sources.map((source) => (
            <tr key={source.name}>
              <td>{source.name}</td>
              <td>{TIER_NAMES[source.tier]}</td>
              <td>{source.weight}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Labels</h2>
      <ul aria-label="Labels">
        <li>
          &ldquo;Confirmed by the company&rdquo;: the affected company published it itself.
          &ldquo;Confirmed by a government agency&rdquo; and &ldquo;Confirmed by security
          researchers&rdquo; name who else confirmed it. &ldquo;Flaw confirmed by &hellip;&rdquo;
          means an advisory confirmed a security flaw, not that anyone was breached.
        </li>
        <li>&ldquo;Reported by N news outlets&rdquo;: news coverage only.</li>
        <li>&ldquo;Claimed by attackers, not confirmed&rdquo;: only the attackers say so.</li>
        <li>&ldquo;Disputed&rdquo;: a later source denied or retracted it.</li>
        <li>&ldquo;Under investigation&rdquo;: reserved; no rule sets it yet.</li>
      </ul>
    </>
  );
}
