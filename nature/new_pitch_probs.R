library(nnet)    
library(dplyr)
library(baseballr)
library(caTools)

df <- statcast_search("2024-04-01", "2024-04-30")

event_df <- df %>%
  mutate(
    result = case_when(
      description == "hit_by_pitch" ~ "single",
      description == "hit_into_play" & events == "single" ~ "single",
      description == "hit_into_play" & events == "double" ~ "double",
      description == "hit_into_play" & events == "triple" ~ "triple",
      description == "hit_into_play" & events == "home_run" ~ "HR",
      description == "hit_into_play" & 
        events %in% c("field_out", "grounded_into_double_play", "force_out", "field_error", "sac_fly", "sac_bunt", "double_play", "fielders_choice", "fielders_choice_out") ~ "out_in_play",
      description == "foul" ~ "foul",
      description %in% c("ball", "blocked_ball") ~ "ball",
      description %in% c("called_strike", "swinging_strike", "swinging_strike_blocked", "foul_tip", "foul_bunt") ~ "strike",
      description %in% c("called_strike", "swinging_strike", "foul_tip") & events == "strikeout" ~ "strikeout",
      TRUE ~ NA_character_
    )
  )

result <- factor(c("ball","strike","foul","out_in_play", "single","double","triple","HR"))

event_df$result <- factor(event_df$result, levels = levels(result))

pitch_class <- factor(c("breaking_ball", "fast_ball", "offspeed"))

pitch_loc <- factor(c("top", "middle", "bottom", "chase"))

event_df <- event_df %>% mutate(
  pitch_class = 
    case_when(
      pitch_type %in% c("CH", "FS", "FO") ~ "offspeed", #changeup, splitter, forkball
      pitch_type %in% c("FF", "FC", "SI") ~ "fastball", #4-seam, cutter, sinker
      pitch_type %in% c("CU", "KC", "SC", "SL", "SV", "ST") ~ "breaking_ball", #curve, knucklecurve, screwball, slider, 
      pitch_type %in% c("KN", "EP") ~ NA #drop euphus and knuckleball pitches!
  )
)

event_df <- event_df %>% mutate(
  pitch_loc = 
    case_when(
      zone %in% c(1, 2, 3) ~ "top", 
      zone %in% c(4,5, 6) ~ "middle", 
      zone %in% c(7,8,9) ~ "bottom",
      zone %in% c(11, 12, 13, 14) ~ "chase"
  )
)

event_df$pitch_class <- factor(event_df$pitch_class, levels = levels(pitch_class))

event_df$pitch_loc <- factor(event_df$pitch_loc, levels = levels(pitch_loc))

event_df <- event_df %>% filter(!is.na(pitch_class), !is.na(pitch_loc))

swing_events <- c(
  "swinging_strike", "swinging_strike_blocked",
  "foul", "foul_tip", "bunt_into_play",
  "hit_into_play", "hit_into_play_no_out", "hit_into_play_score"
)

event_df$swing_take <- with(event_df, description %in% swing_events) 

new_df = event_df %>% select("pitch_class", "pitch_loc", "swing_take", "result")

new_df$result = relevel(new_df$result, ref = "single") # relevel - setting "single as the baseline class

set.seed(1) # for reproducibility of the split!

sample <- sample.split(new_df$result, SplitRatio = 0.75)  #using sample.split function from caTools library

train  <- subset(new_df, sample == TRUE)

test   <- subset(new_df, sample == FALSE)

model <- multinom(result ~ pitch_class + pitch_loc + swing_take, data = train)

summary(model)

# testing the p values of the above model: 
z <- summary(model)$coefficients/summary(model)$standard.errors

p <- (1 - pnorm(abs(z), 0, 1)) * 2

p

pp <- fitted(model) 