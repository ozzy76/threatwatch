import math
import random


def sample_pert(low, mode, high, lmbda=4.0):
    """
    Samples from a Beta-PERT distribution scaled to the [low, high] interval.
    If input arguments are mismatched, handles them gracefully.
    """
    # Force float conversion
    low = float(low)
    mode = float(mode)
    high = float(high)

    if low > high:
        low, high = high, low
    if mode < low:
        mode = low
    elif mode > high:
        mode = high

    range_val = high - low
    if range_val == 0:
        return low

    # Compute Beta-PERT shape parameters alpha and beta
    alpha = 1.0 + lmbda * (mode - low) / range_val
    beta = 1.0 + lmbda * (high - mode) / range_val

    # random.betavariate yields standard Beta(alpha, beta) on [0, 1]
    return low + random.betavariate(alpha, beta) * range_val


def sample_poisson(lam):
    """
    Samples from a Poisson distribution with parameter lambda.
    Uses Knuth's method for low lambda, and Gauss approximation for high lambda.
    """
    lam = float(lam)
    if lam <= 0:
        return 0

    if lam < 30.0:
        L = math.exp(-lam)
        k = 0
        p = 1.0
        while p > L:
            k += 1
            p *= random.random()
        return k - 1
    else:
        # Gaussian approximation for high lambda values
        val = random.gauss(lam, math.sqrt(lam))
        return max(0, int(round(val)))


def run_simulation(inputs: dict, iterations: int = 10000) -> dict:
    """
    Executes a 10,000 iteration Monte Carlo simulation.
    
    Expected inputs dictionary keys:
      - tef: (min, mode, max)
      - vuln: (min, mode, max)
      - primary_loss: (min, mode, max)
      - secondary_loss_freq: (min, mode, max)
      - secondary_loss_mag: (min, mode, max)
      - insurance_premium: float
      - regulatory_penalty_multiplier: float
    """
    tef_range = inputs.get("tef", (0.0, 0.0, 0.0))
    vuln_range = inputs.get("vuln", (0.0, 0.0, 0.0))
    prim_range = inputs.get("primary_loss", (0.0, 0.0, 0.0))
    sec_freq_range = inputs.get("secondary_loss_freq", (0.0, 0.0, 0.0))
    sec_mag_range = inputs.get("secondary_loss_mag", (0.0, 0.0, 0.0))
    
    premium = float(inputs.get("insurance_premium", 0.0))
    reg_mult = float(inputs.get("regulatory_penalty_multiplier", 1.0))

    annual_losses = []

    for _ in range(iterations):
        # 1. Sample Threat Event Frequency (TEF) - events per year
        tef_sampled = sample_pert(*tef_range)
        
        # 2. Sample Vulnerability (Vuln) - probability 0.0 to 1.0
        vuln_sampled = sample_pert(*vuln_range)
        # Clamp Vuln to realistic bounds
        vuln_sampled = max(0.0, min(1.0, vuln_sampled))

        # 3. Derive Loss Event Frequency (LEF) = TEF * Vuln
        lef_sampled = tef_sampled * vuln_sampled

        # 4. Sample annual loss event count via Poisson
        event_count = sample_poisson(lef_sampled)

        run_loss = 0.0

        # 5. Compound losses across all simulated events
        for _ in range(event_count):
            # Sample primary loss
            primary_loss_sampled = sample_pert(*prim_range)
            
            # Sample secondary frequency (likelihood of triggering secondary loss)
            sec_freq_sampled = sample_pert(*sec_freq_range)
            sec_freq_sampled = max(0.0, min(1.0, sec_freq_sampled))

            secondary_loss_sampled = 0.0
            if random.random() < sec_freq_sampled:
                # Sample secondary loss magnitude
                secondary_loss_sampled = sample_pert(*sec_mag_range)
                # Apply regulatory penalty multiplier (authority factor)
                secondary_loss_sampled *= reg_mult

            run_loss += primary_loss_sampled + secondary_loss_sampled

        annual_losses.append(run_loss)

    # Sort results for percentile extraction
    annual_losses.sort()

    # Calculate summary metrics
    min_ale = annual_losses[0]
    max_ale = annual_losses[-1]
    avg_ale = sum(annual_losses) / iterations
    median_ale = annual_losses[iterations // 2]
    var_95 = annual_losses[int(iterations * 0.95)] # Value at Risk

    # 6. Calculate Loss Exceedance Curve (exceedance probability)
    # Define standard dollar threshold markers
    thresholds = [0, 1000, 5000, 10000, 25000, 50000, 100000, 250000, 500000, 1000000, 5000000]
    
    # If maximum loss exceeds $5M, add custom thresholds dynamically
    if max_ale > 5000000:
        thresholds += [10000000, 50000000, 100000000]

    exceedance_curve = {}
    for t in thresholds:
        count = sum(1 for loss in annual_losses if loss > t)
        prob = (count / iterations) * 100.0
        exceedance_curve[str(t)] = round(prob, 2)

    return {
        "min_ale": round(min_ale, 2),
        "max_ale": round(max_ale, 2),
        "avg_ale": round(avg_ale, 2),
        "median_ale": round(median_ale, 2),
        "var_95": round(var_95, 2),
        "loss_exceedance_curve": exceedance_curve,
    }
