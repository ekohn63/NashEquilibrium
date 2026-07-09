suppressPackageStartupMessages({
  library(tidyverse)   # dplyr / tidyr / ggplot2
  library(nnet)        # multinom()
  library(broom)       # tidy() for model objects
  library(tidymodels) 
  library(baseballr)
})

# Pull every pitch thrown in April-2024
apr24 <- scrape_statcast_savant(
  start_date  = "2024-04-01",
  end_date    = "2024-04-30",
  player_type = "pitcher"
)

# Keep only pitches that finished a plate-appearance
apr24 <- apr24 %>%
  filter(!is.na(events))                      # toss warm-ups & nulls

# Save a local copy
write_csv(apr24, "statcast_pitch_events_2024_04.csv")

df <- read_csv("statcast_pitch_events_2024_04.csv") %>%
  mutate(
    ## Collapse pitch types into “Fastball” vs “Offspeed”
    Type = case_when(
      pitch_type %in% c("FF","SI","FC","FO","FA") ~ "Fastball",
      TRUE                                         ~ "Offspeed"
    ),

    ## Bucket vertical location: plate_z ≈ 2 ft = belt
    Location = case_when(
      plate_z <  2.0 ~ "Bottom",
      plate_z <  3.2 ~ "Middle",
      TRUE           ~ "Top"
    ),

    ## Bucket horizontal miss zone (‘Chase’) versus plate
    Location = if_else(zone %in% 11:14, "Chase", Location),

    ## Swing / Take from description column
    BatterAction = if_else(str_detect(description, "swing|foul"), "Swing", "Take"),

    ## Map Statcast events to the nine outcomes we modelled
    Outcome = case_when(
      events == "home_run"   ~ "HR",
      events == "triple"     ~ "Triple",
      events == "double"     ~ "Double",
      events == "single"     ~ "Single",
      events == "field_out"  ~ "Out",
      description %in% c("called_strike")             ~ "Strike",
      description %in% c("swinging_strike",
                         "swinging_strike_blocked",
                         "foul_tip",
                         "foul_bunt")                ~ "Strike",
      description %in% c("blocked_ball",
                         "ball",
                         "pitchout")                 ~ "Ball",
      TRUE                                            ~ NA_character_
    )
  ) %>%
  filter(!is.na(Outcome))                         # drop un-mapped rows





##  Load pitch-by-pitch data ------------------------------------------
#  One row per pitch.  Must include at least:
#  event, p_bucket, b_bucket, count_balls, count_strikes
df <- read_csv("my_pitch_by_pitch.csv")       # <<< EDIT ME: path

##  Basic wrangling ----------------------------------------------------
df <- df %>% 
  mutate(
    event        = factor(event),            # outcome label
    p_bucket     = factor(p_bucket),         # 0…7 – pitch locations / types
    b_bucket     = factor(b_bucket),         # 0 = take, 1 = swing
    state_before = factor(state_before)      # optional: base/out state
  )

##  Choose baseline outcome (“ball” is conventional) -------------------
df$event <- relevel(df$event, ref = "ball")

##  Fit multinomial logistic regression -------------------------------
m_outcome <- multinom(
  event ~ p_bucket + b_bucket + p_bucket:b_bucket +
           count_balls + count_strikes,
  data   = df,
  maxit  = 300,
  trace  = FALSE
)

##  Inspect coefficients (optional) -----------------------------------
tidy(m_outcome) %>%
  arrange(level, desc(abs(estimate))) %>%
  print(n = 40)

##  Build a strategy grid ---------------------------------------------
strategy_grid <- expand.grid(
  p_bucket      = factor(0:7),
  b_bucket      = factor(0:1),
  count_balls   = 0,
  count_strikes = 0,
  KEEP.OUT.ATTRS = FALSE
)

##  Predict outcome probabilities -------------------------------------
prob_mat <- predict(m_outcome,
                    newdata = strategy_grid,
                    type    = "probs")

##  Convert to long form ----------------------------------------------
probs_long <- strategy_grid %>%
  bind_cols(as_tibble(prob_mat)) %>%
  pivot_longer(
    cols      = -c(p_bucket, b_bucket),
    names_to  = "event",
    values_to = "prob"
  )