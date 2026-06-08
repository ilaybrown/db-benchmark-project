SELECT *
FROM benchmark_db.noisy_neighbors
WHERE building_type IN ('Private Home', 'Villa')
  AND day_of_week IN (6, 7)
  AND duration_of_call_min > 30
ORDER BY duration_of_call_min DESC;
