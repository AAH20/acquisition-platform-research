# Wave 1 Research: Auction Theory for Business Sales

**Date:** 2026-10-04
**Focus:** Auction theory applied to business acquisition platforms
**Sources:** 10 web searches, 30 results extracted and synthesized

---

## 1. Auction Theory

Auction theory is the study of how bidders behave and how auction formats perform. It sits at the intersection of game theory (auctions as Bayesian games of incomplete information), mechanism design (auctions as allocation mechanisms), and market microstructure (auctions as models of price formation) [Levin 2004].

**Core environment:** Bidders *i* = 1, ..., *n*; one object to be sold; each bidder observes a private signal *Sᵢ* ~ *F*(·); signals are independent; bidder *i*'s value *vᵢ(sᵢ)* = *sᵢ*. The central question: as the number of bidders grows large, does the auction price converge to the true value of the object? [Levin 2004]

**Key auction formats:**
- **English (ascending):** Open outcry, price rises until one bidder remains. Bidding up to true valuation is the dominant strategy.
- **Dutch (descending):** Price descends until a bidder accepts. Strategically equivalent to first-price sealed-bid; bidders shade down.
- **First-price sealed-bid (FPSB):** Highest bid wins, pays own bid. Bidders shade below true valuation.
- **Second-price sealed-bid (Vickrey):** Highest bid wins, pays second-highest bid. Truth-telling is a weakly dominant strategy.

**Revenue Equivalence Theorem:** Every auction that allocates goods efficiently and offers no profit to a zero-valuation bidder has the same expected profits for every bidder valuation and the same expected revenue for the seller [Milgrom, *Auctions and Bidding: A Primer*].

**Winner's Curse:** In common-value auctions, the bidder with the highest estimate tends to overbid. The winner's curse worsens with more bidders. To avoid it, bidders should assume their signal is the most overly optimistic when bidding [MIT 15.010 Lecture 16].

**Information aggregation:** Auction prices aggregate information of market participants. Pesendorfer and Swinkels (1997) study the loser's curse and information aggregation in auctions [Levin 2004].

---

## 2. Mechanism Design

Mechanism design is the engineering arm of microeconomics — it works backwards from a desired outcome to the rules that produce it when self-interested agents play strategically [maseconomics.com].

**Foundational concepts:**
- **Social choice function:** Maps private information of agents into a collective outcome.
- **Incentive compatibility (IC):** Truth-telling is a best response for every agent. Dominant-strategy IC (truth-telling optimal regardless of others) is the strongest form.
- **Individual rationality (IR):** No agent does worse by participating than by walking away.
- **Revelation Principle (Myerson 1979):** Any outcome implementable by any mechanism can also be implemented by a direct revelation mechanism where agents truthfully report types and truth-telling is a Bayesian-Nash equilibrium.

**Vickrey-Clarke-Groves (VCG) mechanism:** Achieves dominant-strategy IC through externality pricing — each agent pays the externality they impose on others. For a single item, this reduces to the second-price auction. VCG achieves allocative efficiency: the good goes to the bidder with the highest valuation [maseconomics.com].

**Myerson's Optimal Auction (1981):** With regularity conditions on the value distribution, a modified second-price auction with an optimal reserve price maximizes the seller's expected revenue. The optimal reserve price *r*\* = arg max *r*(1 − *F*(*r*)). For regular iid priors, the second-price auction with *n*+1 bidders achieves at least *n*/(*n*+1) of the optimal expected revenue (Bulow-Klemperer theorem) [AGTA Lecture 18; Bulow & Klemperer 1996].

**Generalized Second-Price (GSP) auction:** Used by Google AdWords (launched 2002). Slots allocated by bid × predicted click-through rate. Not strictly truth-revealing, but has stable equilibria (Varian & Edelman 2007). Google generates >$200B annually from ad auctions [maseconomics.com].

**Practical mechanism selection:** Real-world mechanism selection depends on the interplay between theoretical properties, market structure, and computational constraints. GSP achieves O(n log n) time complexity vs VCG's O(nk), providing algorithmic justification for GSP's prevalence in latency-sensitive real-time bidding [bcpublication.org].

**Key assumptions that break in practice:**
1. **Private values** — oil-lease and art auctions have interdependent values; truthful bidding in second-price can lead to winner's curse (Milgrom & Wilson 1982).
2. **Quasi-linear utility** — rules out wealth effects; a bidder with $1M treats a $500K asset the same regardless of net worth.
3. **Risk neutrality** — revenue equivalence fails when bidders are risk-averse [maseconomics.com].

---

## 3. Efficiency and Revenue

**Allocative efficiency:** An auction is efficient if the good is allocated to the bidder who values it most. The Vickrey auction achieves this in dominant strategies. In practice, efficiency outcomes are often far more important than revenue [LSE spectrum auctions analysis].

**Revenue spectrum (UK auctions):** Revenue disparities are dramatic — from £22.5B in the 2000 "biggest auction ever" to £1.4B in 2018 and 2021. The 2021 auction looked "short and sweet" despite low revenue because it achieved both auction and output efficiency [LSE Research Online].

**Optimal reserve price:** Empirical results from California data show the average increase in revenue from using an optimal reserve price is at most 13%. The optimal reserve price is on average 46% larger and tends to reduce the number of successful transactions, but the seller's net profit doubles [BFI WP 2021-142].

**Sequential vs. simultaneous auctions:** Under moderate entry selection and entry costs (2% of average winning bid), a sequential mechanism with jump bidding leads to a 1.8% revenue increase vs 0.2% with simultaneous auctions and an optimal reserve price [BFI WP 2021-142].

**Bid increments:** An increment of 5% is unlikely to lead to significant efficiency concern unless prices reach very high levels [LSE Research Online].

**Resale opportunities:** Empirical evidence strongly supports endogenization of resale opportunities. Resale opportunities affect revenue ranking and efficiency depending on whether bidders observe exits of previous bidders [BFI WP 2021-142].

**Set-aside policies:** A low subsidy (5-6%) suffices for small businesses to win a satisfactory proportion of sales with a 4% price increase, 2% efficiency gain, and slight decrease in large firms' profits [BFI WP 2021-142].

---

## 4. Bidding Strategies

**Private-value strategies:**
- **Second-price / English:** Bid true valuation (dominant strategy).
- **First-price / Dutch:** Shade bid below true valuation. Risk-averse bidders shade less. Optimal bid follows the same shading formula derived for FPSBA [MIT 15.010; bcpub.org].

**Common-value strategies:**
- Account for the winner's curse: assume your signal is the most overly optimistic.
- Bid shading increases with the number of bidders [MIT 15.010].

**Online auction strategies (eBay):**
- **Sniping:** Bidding in the last second. Not predicted by theory but widely observed. Snipers pay a statistically significant amount less than their maximum bid [Yale, Groenwegen 2017].
- **Squatting:** Placing a high bid early. Also allows bidders to pay less than their maximum bid [Yale, Groenwegen 2017].
- **Proxy bidding:** eBay's system allows bidders to set a maximum bid; the system bids incrementally on their behalf. In second-price private-value auctions, bidding true valuation once is the dominant strategy; timing should not matter [Yale, Groenwegen 2017].
- **Equilibrium with sniping:** If *p* > 1/2 [H−L]/[L−m−s], sniping is an equilibrium while non-sniping is not. Auctions with higher starting prices and higher minimum increments see more sniping [Yale, Groenwegen 2017].

**More bidders → more revenue:** With more bidders, both ascending and descending auctions generate more revenue. Ascending: second-highest value increases. Descending: less incentive to shade since it's more likely someone else will jump in [MIT 15.010].

**Auction design affects gaming:** Fixed ending times lead to sniping, which may reduce revenue. Flexible end times (Amazon format: ends once no new bids for 10 minutes) change the strategic landscape [MIT 15.010].

---

## 5. Fraud and Collusion

**Shill bidding:** The act of introducing fake bids into an auction on the seller's behalf to artificially inflate the item's price. The seller can have friends bid or control multiple fake bidder accounts [Trevathan 2018; arxiv.org 1812.10868].

**Real-world cases:**
- **US (2001):** Three men charged for fraudulent bidding in hundreds of art auctions on eBay. Created 40+ user accounts with false registration [Schwartz & Dobrzynski 2002].
- **UK:** A man used two eBay accounts to list a minibus and inflate the price. Fined £5,000 [Williams 2015].

**Aggressive shill bidder characteristics:**
1. Bid exclusively in auctions held by one particular seller.
2. High bid frequency — continually outbid legitimate bids.
3. Few or no winnings (the shill's goal is to lose).
4. Bid within a small time period after a legitimate bid.
5. Bid the minimum amount required to outbid.
6. Bid more near the beginning of the auction [Trevathan 2018].

**Collusive shill bidding strategies:**
1. **Alternating bid strategy:** Two or more shills take alternating turns, lowering β ratings (individual bids per auction).
2. **Alternating auction strategy:** Shills take turns shilling for different auctions, lowering α ratings (auctions participated in).
3. **Hybrid strategy:** Combination of both [Trevathan 2018].

**Detection methods:**
- **Shill Score (Trevathan & Read 2009):** Reputation-based approach assigning a score indicating likelihood of shill behavior. Acts as both detection and deterrent — to avoid detection, a shill must behave like a normal bidder, which stops them from shilling.
- **CSBD algorithm (Majadi et al. 2019):** Uses Local Outlier Factor (LOF) and Belief Propagation (BP) on a bidder-auction graph to detect collusive shill bidding.
- **SPAN (Tsang et al. 2014):** Score Propagation over an Auction Network — identifies 4 feature pairs for buyers and 4 for sellers using Markov Random Fields.
- **Social Network Analysis (Chiu et al. 2011):** Clusters user accounts into groups; labels bidders as suspicious if they have abnormal transactions with sellers and other bidders.
- **Real-time detection (Xu et al. 2009; Majadi et al. 2017):** Tracks activities during the auction and penalizes users based on shill bidding scores at varying stages [doi.org/10.1007/s10614-022-10326-7].

**Anti-shill mechanism design:** A commission fee based on the difference between the winning bid and the seller's reserve can make shill bidding unprofitable. Commission rates are mathematically determined to guarantee non-profitability of shill bidding [docslib.org].

**Collusion in ascending auctions:** Multi-unit ascending and uniform-price auctions are particularly vulnerable to tacit collusion. The Anglo-Dutch auction (hybrid of sealed-bid and ascending) may often perform better [Klemperer, *What Really Matters in Auction Design*].

---

## 6. Bottlenecks and Challenges

**Operational bottlenecks in online auctions:**
- **Fragmented software silos:** Legacy platforms rely on siloed architecture, forcing auction houses to use multiple disconnected programs to prepare, run, and settle a single event.
- **Multi-party coordination:** Auctions require continuous synchronization among consignor/vendor, auctioneer, bidder pool, ultimate buyer, and logistics carrier. Every lot is unique (quantity of one), making automation complex.
- **Administrative burden:** Staff spend 18-24 administrative hours managing the 48-hour window immediately following a sale. Manual coordination of vendor intake forms, sliding-scale consignor matrices, and carrier tracking.
- **Unsold inventory:** Requires manual post-auction offer negotiations via phone and email [auctiondaily.com].

**Cataloging throughput bottleneck:**
- A 300-lot estate takes 15-25 hours to catalog manually, capping solo operators at one sale per week (~50 sales/year).
- AI-powered cataloging tools can reduce a 15-hour session to under 2 hours.
- Companies that solved this bottleneck are scaling; those stuck on manual workflows are losing ground [gavelist.com].

**Spectrum auction bottlenecks:**
- Auctions take months or years to prepare, particularly when federal agencies must coordinate reallocation.
- Coordination bottlenecks among FCC, NTIA, OMB, and other agencies create unnecessary delays.
- Delays in getting licensed spectrum to auction mean reduced consumer benefits [americanactionforum.org].

**Market structure challenges:**
- **Data ownership:** 78% of auctioneers expressed concern that third-party marketplaces use their user data to market competing auctions.
- **Commission-based software:** White-label providers charge 2-5% on online hammer prices, directly impacting profitability as volume scales.
- **Transaction friction:** 64% of digital bidders reported friction due to lack of upfront shipping transparency [auctiondaily.com].

**Industry split:** The auction industry is splitting into growing operators (modernized, multi-platform, AI-powered) and shrinking operators (live-only, manual cataloging, single-platform). 62% of auction transactions now happen online, up from ~50% two years ago [gavelist.com].

---

## 7. Optimization

**Myerson's optimal auction:** For any truthful mechanism, expected revenue equals the expected sum of virtual values. The optimal revenue is bounded by the expected maximum virtual value. For regular iid priors, the optimal auction allocates to the bidder with the highest virtual value (if positive) and charges the critical value [AGTA Lecture 18].

**Optimal ordering in sequential auctions (OOSA):** Deciding the optimal ordering of items to sell in a sequential auction to maximize expected revenue. Two approaches:
1. **Black-box optimization:** Best-first search using learned regression models to evaluate different orderings.
2. **White-box optimization:** Translates models and items into a mixed-integer program (MIP) and runs in an ILP solver (CPLEX) [arxiv.org 1401.1061].

**Machine learning for auction optimization:** Learn regression models from historical auctions to predict expected value of orderings for new auctions. The internal structure of regression models can be efficiently evaluated inside an ILP solver [arxiv.org 1401.1061].

**Reserve price optimization:** Empirical results show optimal reserve prices increase revenue by at most 13% on average, but can double seller's net profit despite reducing transaction volume [BFI WP 2021-142].

**Sequential mechanism optimization:** A new entrant making a jump bid can deter later bidders. Sequential mechanisms generate 1.8% revenue increase vs 0.2% for simultaneous auctions with optimal reserve [BFI WP 2021-142].

---

## 8. NP-Hard Problems

**Winner Determination Problem (WDP):** In combinatorial auctions, choosing the subset of bids that maximizes seller's revenue subject to each good being allocated at most once. Equivalent to weighted set-packing, therefore NP-hard [Leyton-Brown et al., Stanford].

**Optimal mechanism design is NP-hard:** Computing the optimal auction for a single budget-additive bidder whose values are known deterministically and whose budget takes two possible rational values is NP-hard. Unless P=NP, revenue-optimization in very simple multi-item settings can only be tractably approximated [arxiv.org 1211.1703].

**Empirical hardness of WDP:** Particular instances of NP-hard problems can be quite easy in practice. Leyton-Brown, Nudelman, and Shoham (2001) study the empirical hardness of WDP when solved by CPLEX across nine problem distributions. They show that independent features of WDP instances contain enough information to predict CPLEX running time with high accuracy [Stanford, computation.pdf].

**Taming computational complexity:** Two methods proposed:
1. **Anytime algorithm (CASS):** Exploits problem's particular bid structure to reduce search size.
2. **Market-based approach:** Virtual multi-round auction where a virtual agent represents each original bid bundle. Produces allocations that are always optimal or nearly optimal [Fujishima, Leyton-Brown & Shoham 1999].

**Combinatorial auction complexity:** The Clarke-Groves-Vickrey (GVA) mechanism shares the central problem of finding non-conflicting bids that maximize revenue — easily shown to be NP-complete [Rothkopf et al. 1995]. When the number of goods and bids is small enough, exhaustive search can be used; for larger instances, structured search is required.

---

## 9. Machine Learning in Auctions

**Amazon Ads ML stack:** Amazon's Sponsored Products auction uses a generalized second-price mechanism with quality-weighted ranking. The ML stack includes:
- **Prediction stack:** Calibrated click-through rate and conversion predictions.
- **Autobidding theory:** Algorithmic bidding on behalf of advertisers.
- **Reinforcement learning:** For bidding policy optimization.
- **Generative bidding:** Emerging approaches.
- **Noam Brown's search-plus-learning program:** Applied to auction measurement.
- **Learning agents:** Studying whether AI agents collude or not [eternalhorizons.org].

**LLMs as auction participants:** Simulated AI agents (LLMs) with chain-of-thought reasoning agree with experimental literature across classic auction formats:
- LLM bidders produce results consistent with risk-averse human bidders.
- They perform closer to theoretical predictions in obviously strategy-proof auctions.
- They succumb to the winner's curse in common value settings.
- 1,000+ auctions run for less than $400 with GPT-4 models — three orders of magnitude cheaper than modern auction experiments [arxiv.org 2507.09083].

**ML-powered combinatorial auctions (MLHCA):** Machine Learning-powered Hybrid Combinatorial Auction uses both value queries (VQs) and demand queries (DQs):
- Reduces efficiency loss by up to a factor of 10 vs previous SOTA.
- Requires 42% fewer queries than BOCA and 26% fewer than ML-CCA.
- Bidders do not need to decide which bundles to bid for — the auction automatically suggests bundles.
- Efficiency improvements correspond to welfare gains of hundreds of millions of USD [openreview.net].

**ML for auction design:** Learning regression models from historical auction data to predict expected value of orderings, then using these models inside ILP solvers for optimization [arxiv.org 1401.1061].

**FTC vs Amazon (2026):** FTC and 22 states sued Amazon over how its auctions price clicks. Amazon disclosed that ~92% of Sponsored Products placements in 2024 did not go to the highest bidder, and the mean winning bid ranked around 128th by amount [eternalhorizons.org].

---

## 10. Market Design

**Auction design is "horses for courses":** The most important issues in auction design are the traditional concerns of competition policy — preventing collusive, predatory, and entry-deterring behaviour. Everything depends on the details of the context [Klemperer, *What Really Matters in Auction Design*].

**Ascending vs. sealed-bid:** Ascending and uniform-price auctions are particularly vulnerable to collusion. The Anglo-Dutch auction (hybrid) may often perform better. A sealed-bid component might introduce inefficiency in allocation among winners [Klemperer].

**Market structure is critical:** In designing auctions that create new markets, market structure issues are paramount. The UK 3G auction design allowed strong established players to partner with local incumbents, resulting in a concentrated (six-firm) market. The Italian design failed to recognize the importance of final market structure [Klemperer].

**Spectrum auctions as market design:** The FCC's simultaneous multiple-round (SMR) auction, designed by Milgrom, Wilson, and Preston McAfee, allowed bidders to learn about competitors' valuations across rounds. Between 1994 and 2024, FCC auctions raised more than $230 billion. The 2017 incentive auction used forward and reverse auction in tandem, raising $19.8 billion [maseconomics.com].

**Platform economics:** Mechanism design moved from academic curiosity to industrial infrastructure between 1995 and 2010. Google's AdWords (GSP), Meta's ad system, and ride-sharing surge pricing (Uber/Lft) are all mechanism design applications. The mechanism is the business [maseconomics.com].

**Real estate auction marketplaces:** Online platforms connect buyers, sellers, and brokers. Licensed brokers post upcoming auctions; buyers search nationwide for properties. The marketplace empowers brokers to expand market visibility and maximize online exposure [realestateauction.com].

**Auction industry growth:** The auction house market is projected to grow from $38.7B in 2026 to $60.9B by 2035. HiBid auctioneers sold nearly $2B in inventory over 12 months. 80% of Christie's bids are now placed digitally [gavelist.com].

---

## 11. Citations

1. Levin, Jonathan (2004). "Auction Theory." Stanford University, Econ 286. http://web.stanford.edu/~jdlevin/Econ%20286/Auctions.pdf
2. Milgrom, Paul. "Auctions and Bidding: A Primer." https://web.stanford.edu/~milgrom/publishedarticles/Auctions%20and%20Bidding%20Primer.pdf
3. Milgrom, Paul and Robert Weber (1982). "A Theory of Auctions and Competitive Bidding." *Econometrica*, 50.
4. Vickrey, William (1961). "Counterspeculation, Auctions and Competitive Sealed Tenders." *Journal of Finance*, 16, 8-39.
5. Myerson, Roger (1981). "Optimal Auction Design." *Mathematics of Operations Research*, 6, 58-73.
6. Riley, John and William Samuelson (1981). "Optimal Auction." *American Economic Review*, 71, 381-392.
7. Bulow, Jeremy and Paul Klemperer (1996). "Auctions vs. Negotiations." *American Economic Review*.
8. Klemperer, Paul. "What Really Matters in Auction Design." https://www.nuff.ox.ac.uk/economics/papers/2000/w26/Design.pdf
9. Pesendorfer, Wolfgang and Jeroen Swinkels (1997). "The Loser's Curse and Information Aggregation in Auctions." *Econometrica*, 65.
10. Wilson, Robert (1977). "A Bidding Model of Perfect Competition." *Review of Economic Studies*.
11. Wilson, Robert (1992). "Strategic Analysis of Auctions." *Handbook of Game Theory*.
12. Milgrom, Paul (2003). *Putting Auction Theory to Work*. Cambridge University Press.
13. Milgrom, Paul and Ilya Segal (2002). "Envelope Theorems for Arbitrary Choice Sets." *Econometrica*, 70, 583-601.
14. Ausubel, Lawrence M. and Paul R. Milgrom. "Ascending Auctions with Package Bidding." http://www.bepress.com/bejte
15. Varian, Hal and Benjamin Edelman (2007). "Google's AdWords auction." 
16. Leyton-Brown, Kevin, Eugene Nudelman, and Yoav Shoham. "Learning the Empirical Hardness of Optimization Problems: The case of combinatorial auctions." Stanford University. http://robotics.stanford.edu/~kevinlb/computation.pdf
17. Fujishima, Y., Leyton-Brown, K., and Shoham, Y. (1999). "Taming the computational complexity of combinatorial auctions: Optimal and approximate approaches." *IJCAI-99*. http://robotics.stanford.edu/~kevinlb/cass_vsa.pdf
18. Rothkopf, M. et al. (1995). "Computationally manageable combinatorial auctions." 
19. Trevathan, Jarrod (2018). "Detecting Collusive Shill Bidding in Commercial Online Auctions." https://doi.org/10.1007/s10614-022-10326-7
20. Trevathan, Jarrod and Read, W. (2009). "Shill Score" detection system.
21. Majadi, N., Trevathan, J., and Bergmann, N. (2019). "Collusive Shill Bidding Detection (CSBD) algorithm."
22. Tsang et al. (2014). "SPAN: Score Propagation over an Auction Network."
23. Chiu et al. (2011). "Social Network Analysis for auction fraud detection."
24. Xu et al. (2009) and Majadi et al. (2017). "Real-time shill bidding detection."
25. Groenwegen, Philip (2017). "Squatting, Sniping, and Online Strategy: Analyzing Early and Late Bidding in eBay Auctions." Yale University. https://economics.yale.edu/sites/default/files/2023-01/PhilipGroenwegen_Senior%20Essay.pdf
26. MIT 15.010 (2004). "Lecture 16: Auctions and Bidding." https://ocw.mit.edu/courses/15-010-economic-analysis-for-business-decisions-fall-2004/7bf8a0e7391fff2f7952d86020567632_auctions_bidding.pdf
27. "The Complexity of Optimal Mechanism Design." https://arxiv.org/abs/1211.1703v1
28. "Auction optimization with models learned from data." https://arxiv.org/pdf/1401.1061
29. "Learning from Synthetic Labs: Language Models as Auction Participants." https://arxiv.org/pdf/2507.09083v1
30. "Prices, Bids, Values: One ML-Powered Combinatorial Auction to Rule Them All." https://openreview.net/pdf?id=4ViG4gQD3i
31. "Mechanism Design Economics: Engineering Outcomes from Auctions to Matching Markets." https://maseconomics.com/mechanism-design-economics-engineering-outcomes-from-auctions-to-matching-markets
32. "Bidding Strategy and Auction Design." https://docslib.org/doc/1805838/bidding-strategy-and-auction-design
33. "The Efficiency Gap: Analyzing The Operational And Financial Friction In Modern Online Auctions." https://auctiondaily.com/news/the-efficiency-gap-analyzing-the-operational-and-financial-friction-in-modern-online-auctions/
34. "Spectrum Auctions and the Reallocation Bottleneck." https://www.americanactionforum.org/insight/spectrum-auctions-reallocation/
35. "The Auction Industry Is Splitting in Two." https://gavelist.com/blog/why-some-estate-auction-companies-are-growing-while-others-are-shrinking
36. "AGTA - Lecture 18 - Optimal Auctions." https://opencourse.inf.ed.ac.uk/sites/default/files/2026-03/agta_-_lecture_18_-_optimal_auctions.pdf
37. "Optimal Auction Design." *Mathematics of Operations Research*. https://dl.acm.org/doi/10.1287/moor.6.1.58
38. "A Day on Amazon Ads: Auctions, Bidding, and the Machines That Learn Them." https://eternalhorizons.org/reading/amazon-ads
39. "Empirical Perspectives on Auctions." BFI Working Paper 2021-142. https://bfi.uchicago.edu/wp-content/uploads/2021/11/BFI_WP_2021-142-1.pdf
40. "Auction bidding and outcomes." LSE Research Online. https://researchonline.lse.ac.uk/id/eprint/118248/1/Myers_spectrum_auctions_12_auction_bidding_and_outcomes_published.pdf
41. "Detecting Multiple Seller Collusive Shill Bidding." https://sciencedirect.com/science/article/pii/S1567422321000387
42. "Detecting Multiple Seller Collusive Shill Bidding." https://arxiv.org/html/1812.10868v1
43. "Evolution of auction design from ancient traditions to modern digital markets." https://bcpublication.org/index.php/SJEMR/article/download/9304/9239/12572
44. Hendricks, K., Porter, R., and Boudreau, B. (1987). "Empirical predictions of auction theory: OCS lease sales."
45. Hendricks, K. and Porter, R. (1987). "Empirical predictions of auction theory."
46. Athey, S., Coey, D., and Levin, J. (2013). "Set-aside policies in USFS auctions."
47. David, E. et al. (2007). "Costs of the auctioneer, revenue, and auction efficiency for online auctions."
48. Bajari, P. and Hortaçsu, A. (2003). "Online auction bidding strategies."
49. Roth, A. and Ockenfels, A. (2000). "Last-minute bidding in eBay auctions."
50. Schwartz, J. and Dobrzynski, J. (2002). "US shill bidding case." 
51. Williams (2015). "UK shill bidding case."
52. Snyder (1999). "Shill bidding penalties."
53. Dolan and Agent (2004). "Shill bidding enforcement."
54. Kauffman, R. and Wood, C. (2003, 2005). "Shill bidding detection."
55. Barbaro, S. and Bracht, B. (2004). "Auction fraud detection."
56. Cheng, M. and Xu, Y. (2006). "Auction fraud detection."
57. Gregg, D. and Scott, J. (2008). "Shill bidding."
58. Kaur, R. and Garg, S. (2015). "Auction fraud types."
59. Trevathan, J. and Read, W. (2007a, 2007b). "Collusive shill bidding strategies."
60. Majadi, N. and Trevathan, J. (2018). "Real-time collusive shill bidding detection."
61. Brero, G. et al. (2018, 2021). "ML-powered iterative combinatorial auctions."
62. Weissteiner, M. and Seuken, S. (2020, 2022, 2023). "ML-based preference elicitation in CAs."
63. Blum, A. et al. (2004). "Preference elicitation as a learning problem."
64. Lahaie, S. and Parkes, D. (2004). "Preference elicitation in CAs."
65. Ausubel, L. and Baranov, O. (2017). "Value of goods traded in CAs."

---

## Summary Table

| Topic | Key Finding | Primary Source |
|-------|-------------|----------------|
| Auction Theory | Revenue equivalence: all efficient auctions yield same expected revenue | Milgrom, Primer |
| Mechanism Design | Vickrey auction achieves dominant-strategy IC; Myerson's optimal auction maximizes revenue | Myerson 1981; Vickrey 1961 |
| Efficiency | Optimal reserve price increases revenue ≤13% but doubles net profit | BFI WP 2021-142 |
| Bidding Strategies | Sniping and squatting are equilibrium strategies in online auctions | Groenwegen 2017 |
| Fraud/Collusion | Shill Score and CSBD algorithms detect collusive shill bidding | Trevathan 2018; Majadi 2019 |
| Bottlenecks | Cataloging throughput caps solo operators at 1 sale/week | gavelist.com |
| Optimization | ML + ILP solves optimal ordering in sequential auctions | arxiv 1401.1061 |
| NP-Hard Problems | Winner determination is NP-hard; optimal mechanism design is NP-hard | Leyton-Brown; arxiv 1211.1703 |
| Machine Learning | LLMs replicate human bidding behavior; MLHCA reduces efficiency loss 10× | arxiv 2507.09083; openreview |
| Market Design | "Horses for courses" — design must match context; collusion prevention paramount | Klemperer |
