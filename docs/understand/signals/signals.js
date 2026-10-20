/* Conditional teaching models; no measured data, fitting, or autoplay. */
"use strict";

(function () {
  const yearDays = 365.25;
  const tauCircle = 2 * Math.PI;
  const constants = Object.freeze({
    kappa0: 1e-18,
    gamma: 1e-18,
    mu: 1e-16,
    temperature: 300,
    kB: 1.380649e-23
  });

  function bounded(value, minimum, maximum, name) {
    if (!Number.isFinite(value) || value < minimum || value > maximum) {
      throw new RangeError(name + " must be finite and between " + minimum + " and " + maximum + ".");
    }
    return value;
  }

  function modulation(value) {
    return bounded(value, 0, 1, "Modulation");
  }

  function annualPhase(value) {
    return bounded(value, -Math.PI, Math.PI, "Annual phase");
  }

  function am(tDays, m, phaseRadians) {
    bounded(tDays, 0, 2 * yearDays, "Time in solar days");
    modulation(m);
    annualPhase(phaseRadians);
    return (1 + m * Math.cos(tauCircle * tDays / yearDays + phaseRadians)) * Math.cos(tauCircle * tDays);
  }

  function components(m, phaseRadians) {
    modulation(m);
    annualPhase(phaseRadians);
    return [
      { frequency: 1 - 1 / yearDays, amplitude: m / 2, phase: -phaseRadians },
      { frequency: 1, amplitude: 1, phase: 0 },
      { frequency: 1 + 1 / yearDays, amplitude: m / 2, phase: phaseRadians }
    ];
  }

  function sensor(ratio) {
    bounded(ratio, 0.1, 2, "Stiffness ratio");
    const kappa = constants.kappa0 * ratio;
    const kBT = constants.kB * constants.temperature;
    return {
      kappa: kappa,
      gamma: constants.gamma,
      mu: constants.mu,
      temperature: constants.temperature,
      kBT: kBT,
      tau: constants.gamma / kappa,
      cutoff: kappa / (tauCircle * constants.gamma),
      variance: kBT / kappa,
      staticGain: constants.mu / kappa,
      inputPSD: 4 * kBT * constants.gamma / (constants.mu * constants.mu)
    };
  }

  function response(fHz, ratio) {
    bounded(fHz, 0, Number.MAX_VALUE, "Frequency in Hz");
    const model = sensor(ratio);
    // Multiply by the small damping coefficient first, including at huge f.
    const damping = (tauCircle * model.gamma) * fHz;
    return {
      gain: model.mu / Math.hypot(model.kappa, damping),
      phase: -Math.atan2(damping, model.kappa)
    };
  }

  function outputPSD(fHz, ratio) {
    bounded(fHz, 0, Number.MAX_VALUE, "Frequency in Hz");
    const model = sensor(ratio);
    const denominator = Math.hypot(model.kappa, (tauCircle * model.gamma) * fHz);
    // Squaring the ASD avoids overflowing the squared denominator.
    const asd = Math.sqrt(4 * model.kBT * model.gamma) / denominator;
    return asd * asd;
  }

  function bandVariance(fMax, ratio) {
    bounded(fMax, 0, Number.MAX_VALUE, "Upper bandwidth in Hz");
    const model = sensor(ratio);
    const angle = Math.atan2((tauCircle * model.gamma) * fMax, model.kappa);
    return (2 * model.kBT / (Math.PI * model.kappa)) * angle;
  }

  function step(tSec, ratio, field = 1e-4) {
    bounded(tSec, 0, Number.MAX_VALUE, "Time in seconds");
    bounded(field, 0, 1e-3, "Step field in tesla");
    const model = sensor(ratio);
    // expm1 retains small-time accuracy; an infinite t/tau has limit one.
    return model.staticGain * field * -Math.expm1(-tSec / model.tau);
  }

  const SignalModels = Object.freeze({
    yearDays: yearDays,
    am: am,
    components: components,
    sensor: sensor,
    response: response,
    outputPSD: outputPSD,
    bandVariance: bandVariance,
    step: step
  });

  if (typeof module !== "undefined" && module.exports) {
    module.exports = SignalModels;
  }
  if (typeof globalThis !== "undefined") {
    globalThis.SignalModels = SignalModels;
  }
  if (typeof document === "undefined") return;

  function initialize() {
    const nodes = {};
    const ids = [
      "am-controls", "sensor-controls", "modulation", "annual-phase", "season",
      "stiffness", "duration", "bandwidth", "annual-envelope", "time-signal",
      "time-envelope", "time-envelope-negative", "modulation-value", "annual-phase-value",
      "season-value", "time-start", "time-end", "am-summary", "step-curve", "gain-curve",
      "noise-curve", "step-curve-reference", "gain-curve-reference", "noise-curve-reference",
      "stiffness-value", "duration-value", "bandwidth-value", "gain-value", "rms-value",
      "tau-value", "cutoff-value", "band-rms", "noise-floor", "step-end", "sensor-summary"
    ];
    for (let i = 0; i < 3; i += 1) {
      ids.push("component-" + i, "component-amplitude-" + i, "component-phase-" + i);
    }

    function text(id, value) {
      nodes[id].textContent = value;
    }

    function value(id, minimum, maximum) {
      return bounded(Number(nodes[id].value), minimum, maximum, id);
    }

    function three(value) {
      return value.toPrecision(3);
    }

    function draw(id, count, coordinate) {
      const points = [];
      for (let i = 0; i <= count; i += 1) {
        const u = i / count;
        const x = 54 + 520 * u;
        const y = coordinate(u);
        points.push((i === 0 ? "M" : "L") + x.toFixed(3) + "," + y.toFixed(3));
      }
      nodes[id].setAttribute("d", points.join(""));
    }

    function updateAM() {
      const m = value("modulation", 0, 1);
      const degrees = value("annual-phase", -180, 180);
      const phase = degrees * Math.PI / 180;
      const season = value("season", 0, 360);
      const envelope = function (t) {
        return 1 + m * Math.cos(tauCircle * t / yearDays + phase);
      };
      draw("annual-envelope", 240, function (u) { return 176 - 70 * envelope(yearDays * u); });
      draw("time-signal", 400, function (u) { return 110 - 40 * am(season + 5 * u, m, phase); });
      draw("time-envelope", 120, function (u) { return 110 - 40 * envelope(season + 5 * u); });
      draw("time-envelope-negative", 120, function (u) { return 110 + 40 * envelope(season + 5 * u); });
      components(m, phase).forEach(function (component, i) {
        nodes["component-" + i].setAttribute("y2", (176 - 130 * component.amplitude).toFixed(3));
        text("component-amplitude-" + i, three(component.amplitude));
        text("component-phase-" + i, three(component.phase) + " rad");
      });
      text("modulation-value", three(m));
      text("annual-phase-value", three(degrees) + "°");
      text("season-value", three(season) + " days");
      text("time-start", three(season));
      text("time-end", three(season + 5));
      text("am-summary", "Synthetic analytical signal: modulation " + three(m) +
        ", annual phase " + three(degrees) + " degrees. The carrier cosine amplitude is 1; the lower and upper sideband amplitudes are each " +
        three(m / 2) + ". The time view covers solar days " + three(season) + " to " + three(season + 5) +
        ". Changing annual phase changes the sideband phases, not their amplitudes or frequencies. These are specified components, not measured spectral peaks.");
    }

    function updateSensor() {
      const ratio = value("stiffness", 0.1, 2);
      const duration = value("duration", 0.2, 30);
      const bandwidth = value("bandwidth", 0.01, 2);
      const model = sensor(ratio);
      const bandRMS = Math.sqrt(bandVariance(bandwidth, ratio));
      const inputASD = Math.sqrt(model.inputPSD);
      const elapsed = duration / model.tau;
      const settled = -Math.expm1(-elapsed);
      [ { ratio: ratio, suffix: "" }, { ratio: 1, suffix: "-reference" } ].forEach(function (curve) {
        draw("step-curve" + curve.suffix, 240, function (u) {
          return 176 - 140 * step(duration * u, curve.ratio) / 0.1;
        });
        draw("gain-curve" + curve.suffix, 240, function (u) {
          const frequency = Math.pow(10, -3 + 4 * u);
          return 176 - 35 * (Math.log10(response(frequency, curve.ratio).gain) + 1);
        });
        draw("noise-curve" + curve.suffix, 240, function (u) {
          const frequency = Math.pow(10, -3 + 4 * u);
          return 176 - 20 * (Math.log10(outputPSD(frequency, curve.ratio)) + 6);
        });
      });
      text("stiffness-value", three(ratio) + " × reference");
      text("duration-value", three(duration) + " s");
      text("bandwidth-value", three(bandwidth) + " Hz");
      text("gain-value", three(model.staticGain) + " rad/T");
      text("rms-value", three(Math.sqrt(model.variance)) + " rad");
      text("tau-value", three(model.tau) + " s");
      text("cutoff-value", three(model.cutoff) + " Hz");
      text("band-rms", three(bandRMS) + " rad");
      text("noise-floor", three(model.inputPSD) + " T²/Hz; amplitude density " + three(inputASD) + " T/√Hz");
      text("step-end", three(duration));
      text("sensor-summary", "Conditional equilibrium model: stiffness is " + three(ratio) +
        " times the reference. Static gain is " + three(model.staticGain) + " radians per tesla; full thermal RMS is " +
        three(Math.sqrt(model.variance)) + " radians. Relaxation time is " + three(model.tau) +
        " seconds and cutoff is " + three(model.cutoff) + " hertz. The " + three(duration) +
        " second observation spans " + three(elapsed) + " relaxation times; the mean step response reaches " +
        three(100 * settled) + "% of its final value. Output RMS in the ideal zero-to-" + three(bandwidth) +
        " hertz band is " + three(bandRMS) + " radians. The input-equivalent thermal amplitude spectral density remains " +
        three(inputASD * 1e6) + " microtesla per square root hertz at every stiffness. Dashed curves show reference stiffness on the same axes.");
    }

    try {
      ids.forEach(function (id) {
        nodes[id] = document.getElementById(id);
        if (!nodes[id]) throw new Error("Missing explainer element: " + id);
      });
      updateAM();
      updateSensor();
      ["modulation", "annual-phase", "season"].forEach(function (id) {
        nodes[id].addEventListener("input", updateAM);
      });
      ["stiffness", "duration", "bandwidth"].forEach(function (id) {
        nodes[id].addEventListener("input", updateSensor);
      });
      nodes["am-controls"].disabled = false;
      nodes["sensor-controls"].disabled = false;
    } catch (error) {
      // Keep the written explanations and default diagrams usable if setup fails.
      if (typeof console !== "undefined" && console.error) {
        console.error("Signal explainers remain in their static fallback.", error);
      }
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize);
  } else {
    initialize();
  }
}());
