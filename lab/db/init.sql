-- Synthetic data only. Every name, date and number below is invented.
CREATE TABLE patients (
    id            SERIAL PRIMARY KEY,
    facility_id   INT  NOT NULL,
    full_name     TEXT NOT NULL,
    date_of_birth DATE NOT NULL,
    ward          TEXT,
    created_by    TEXT NOT NULL DEFAULT 'seed',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE appointments (
    id            SERIAL PRIMARY KEY,
    facility_id   INT  NOT NULL,
    patient_id    INT  NOT NULL REFERENCES patients(id),
    scheduled_for TIMESTAMPTZ NOT NULL,
    clinic        TEXT NOT NULL,
    reason        TEXT,
    created_by    TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ON patients (facility_id);
CREATE INDEX ON appointments (facility_id);

-- Facility 1: ids 1-6. Facility 2: ids 7-10 (used to prove cross-facility access returns 404).
INSERT INTO patients (facility_id, full_name, date_of_birth, ward) VALUES
  (1, 'Achieng Synthetic',  '1988-03-14', 'Maternity'),
  (1, 'Mutua Testcase',     '1975-11-02', 'Medical'),
  (1, 'Njeri Example',      '2001-07-21', 'Outpatient'),
  (1, 'Kiprono Sample',     '1964-01-30', 'Surgical'),
  (1, 'Wairimu Dummy',      '1993-05-09', 'Medical'),
  (1, 'Omondi Placeholder', '2015-12-17', 'Paediatrics'),
  (2, 'Chebet Fictional',   '1980-09-05', 'Medical'),
  (2, 'Barasa Invented',    '1970-04-22', 'Surgical'),
  (2, 'Akinyi Mock',        '1999-02-11', 'Maternity'),
  (2, 'Kariuki Fake',       '1958-08-28', 'Outpatient');

INSERT INTO appointments (facility_id, patient_id, scheduled_for, clinic, reason, created_by) VALUES
  (1, 1, now() + interval '2 days', 'Antenatal',  'Routine visit',  'seed'),
  (1, 3, now() + interval '3 days', 'General',    'Follow-up',      'seed'),
  (2, 7, now() + interval '1 day',  'Diabetes',   'Review',         'seed');
