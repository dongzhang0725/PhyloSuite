params = {
  "general": {
    "label": "General",
    "fields": {
      "number_of_guesses": {
        "label":    "Number of guesses",
        "doc":      "How many times to solve the problem.",
        "type":     "int",
        "default":  1
      },
      "perturb_factor": {
        "label":    "Perturb Factor",
        "doc":      "Maximum perturbation percent between different guesses.",
        "type":     "float",
        "default":  0.01
      },
      "largeval": {
        "label":    "Large value",
        "doc":      "Internal. For clamping. Should be infinitely large.",
        "type":     "float",
        "default":  1e30
      },
      "seed": {
        "label":    "Seed",
        "doc":      "Seed for the random number generator. Use system time if zero.",
        "type":     "int",
        "default":  0
      },
      "scalar": {
        "label":    "Scalar",
        "doc":      "Force root age at 1.0 and ignore all constraints.",
        "type":     "bool",
        "default":  False
      }
    }
  },
  "branch_length": {
    "label": "Branch Length",
    "fields": {
      "format": {
        "label":    "Format",
        "doc":      "Persite: lengths in units of numbers of substitutions per site.\nTotal: lengths have units of total numbers of substitutions.\nGuess: use rouch estimate based on maximum branch length.",
        "type":     "list",
        "default":  "persite",
        "data": {
          "items":  ["total", "persite", "guess"],
          "labels": ["Total", "Per Site", "Guess"]
          }
      },
      "nsites": {
        "label":    "Subs per site",
        "doc":      "Number of sites in sequences that branch lengths on input trees were calculated from.",
        "type":     "int",
        "default":  1
      },
      "round": {
        "label":    "Round",
        "doc":      "Discard fractional part. If False, takes longer to diverge.",
        "type":     "bool",
        "default":  True
      }
    }
  },
  "barrier": {
    "label": "Barrier",
    "fields": {
      "manual": {
        "label":    "Manual",
        "doc":      "True uses original barrier method. Auto uses scipy, doesn't work",
        "type":     "bool",
        "default":  True
      },
      "max_iterations": {
        "label":    "Max Iterations",
        "doc":      "Maximum allowed number of iterations for relaxed constrained optimization.",
        "type":     "int",
        "default":  10
      },
      "initial_factor": {
        "label":    "Initial Factor",
        "doc":      "Internal. Initial Factor.",
        "type":     "float",
        "default":  0.25
      },
      "multiplier": {
        "label":    "Multiplier",
        "doc":      "Internal. Multiplier.",
        "type":     "float",
        "default":  0.10
      },
      "tolerance": {
        "label":    "Tolerance",
        "doc":      "Internal. Tolerance.",
        "type":     "float",
        "default":  0.0001
      }
    }
  },
  "method": {
    "label": "Method",
    "fields": {
      "method": {
        "label":    "Method",
        "doc":      "Objective function for optimization.",
        "type":     "list",
        "default":  "nprs",
        "data": {
          "items":  ["nprs"],
          "labels": ["NPRS"]
          }
      },
      "exponent": {
        "label":    "Exponent",
        "doc":      "Exponent used in NPRS objective function.",
        "type":     "int",
        "default":  2
      },
      "logarithmic": {
        "label":    "Logarithmic",
        "doc":      "Logarithmic rate differences.",
        "type":     "bool",
        "default":  False
      }
    }
  },
  "algorithm": {
    "label": "Algorithm",
    "fields": {
      "algorithm": {
        "label":    "Algorithm",
        "doc":      "Algorithm used for optimization.",
        "type":     "list",
        "default":  "powell",
        "data": {
          "items":  ["powell"],
          "labels": ["Powell"]
          }
      },
      "variable_tolerance": {
        "label":    "Variable tolerance",
        "doc":      "Powell variable tolerance.",
        "type":     "float",
        "default":  1e-8
      },
      "function_tolerance": {
        "label":    "Function tolerance",
        "doc":      "Powell function tolerance.",
        "type":     "float",
        "default":  1e-8
      }
    }
  }
}
