-- Stage 2 correction: reject contradictory journey stage and timing records.

begin;

alter table public.journey_states
  drop constraint if exists journey_states_timing_source_check,
  drop constraint if exists journey_states_postpartum_day_check,
  drop constraint if exists journey_states_check2,
  drop constraint if exists journey_states_check3,
  drop constraint if exists journey_states_check4;

alter table public.journey_states
  add constraint journey_states_timing_source_check check (timing_source in (
    'user_reported_possible_pregnancy',
    'document_estimated_due_date', 'user_estimated_due_date',
    'manual_week_day', 'approximate_month_range',
    'delivery_date', 'postpartum_week'
  )),
  add constraint journey_states_postpartum_day_check
    check (postpartum_day between 0 and 6),
  add constraint journey_states_stage_timing_check check (
    (
      stage = 'possible_pregnancy'
      and timing_source = 'user_reported_possible_pregnancy'
      and gestational_week is null
      and gestational_day is null
      and postpartum_week is null
      and postpartum_day is null
      and estimated_due_date is null
      and delivery_date is null
      and approximate_month_min is null
      and approximate_month_max is null
    )
    or
    (
      stage = 'pregnancy'
      and postpartum_week is null
      and postpartum_day is null
      and delivery_date is null
      and (
        (
          timing_source = 'manual_week_day'
          and gestational_week is not null
          and gestational_day is not null
          and estimated_due_date is null
          and approximate_month_min is null
          and approximate_month_max is null
        )
        or
        (
          timing_source in ('document_estimated_due_date', 'user_estimated_due_date')
          and gestational_week is not null
          and gestational_day is not null
          and estimated_due_date is not null
          and approximate_month_min is null
          and approximate_month_max is null
        )
        or
        (
          timing_source = 'approximate_month_range'
          and gestational_week is null
          and gestational_day is null
          and estimated_due_date is null
          and approximate_month_min is not null
          and approximate_month_max is not null
        )
      )
    )
    or
    (
      stage = 'postpartum'
      and gestational_week is null
      and gestational_day is null
      and estimated_due_date is null
      and approximate_month_min is null
      and approximate_month_max is null
      and postpartum_week is not null
      and postpartum_day is not null
      and (
        (timing_source = 'delivery_date' and delivery_date is not null)
        or
        (timing_source = 'postpartum_week' and delivery_date is null)
      )
    )
  );

comment on constraint journey_states_stage_timing_check on public.journey_states is
  'Only fields required by the selected stage and timing source may be populated.';

commit;
