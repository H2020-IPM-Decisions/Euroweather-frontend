-- Adding the aggregation type to parameter

ALTER TABLE parameter 
ADD COLUMN aggregation_type varchar(31);

UPDATE parameter SET aggregation_type = 'AVG' WHERE parameter_id = 1001;
UPDATE parameter SET aggregation_type = 'AVG' WHERE parameter_id = 1002;
UPDATE parameter SET aggregation_type = 'MIN' WHERE parameter_id = 1003;
UPDATE parameter SET aggregation_type = 'MAX' WHERE parameter_id = 1004;
UPDATE parameter SET aggregation_type = 'AVG' WHERE parameter_id = 1021;
UPDATE parameter SET aggregation_type = 'AVG' WHERE parameter_id = 1022;
UPDATE parameter SET aggregation_type = 'MIN' WHERE parameter_id = 1023;
UPDATE parameter SET aggregation_type = 'MAX' WHERE parameter_id = 1024;
UPDATE parameter SET aggregation_type = 'AVG' WHERE parameter_id = 1101;
UPDATE parameter SET aggregation_type = 'AVG' WHERE parameter_id = 1102;
UPDATE parameter SET aggregation_type = 'AVG' WHERE parameter_id = 1111;
UPDATE parameter SET aggregation_type = 'AVG' WHERE parameter_id = 1112;
UPDATE parameter SET aggregation_type = 'AVG' WHERE parameter_id = 1121;
UPDATE parameter SET aggregation_type = 'AVG' WHERE parameter_id = 1122;
UPDATE parameter SET aggregation_type = 'AVG' WHERE parameter_id = 1131;
UPDATE parameter SET aggregation_type = 'AVG' WHERE parameter_id = 1132;
UPDATE parameter SET aggregation_type = 'AVG' WHERE parameter_id = 1141;
UPDATE parameter SET aggregation_type = 'AVG' WHERE parameter_id = 1142;
UPDATE parameter SET aggregation_type = 'AVG' WHERE parameter_id = 1151;
UPDATE parameter SET aggregation_type = 'AVG' WHERE parameter_id = 1152;
UPDATE parameter SET aggregation_type = 'SUM' WHERE parameter_id = 2001;
UPDATE parameter SET aggregation_type = 'AVG' WHERE parameter_id = 3001;
UPDATE parameter SET aggregation_type = 'AVG' WHERE parameter_id = 3002;
UPDATE parameter SET aggregation_type = 'MIN' WHERE parameter_id = 3003;
UPDATE parameter SET aggregation_type = 'MAX' WHERE parameter_id = 3004;
UPDATE parameter SET aggregation_type = 'AVG' WHERE parameter_id = 3021;
UPDATE parameter SET aggregation_type = 'AVG' WHERE parameter_id = 3022;
UPDATE parameter SET aggregation_type = 'MIN' WHERE parameter_id = 3023;
UPDATE parameter SET aggregation_type = 'MAX' WHERE parameter_id = 3024;
UPDATE parameter SET aggregation_type = 'SUM' WHERE parameter_id = 3101;
UPDATE parameter SET aggregation_type = 'SUM' WHERE parameter_id = 3102;
UPDATE parameter SET aggregation_type = 'SUM' WHERE parameter_id = 3103;
UPDATE parameter SET aggregation_type = 'AVG' WHERE parameter_id = 4001;
UPDATE parameter SET aggregation_type = 'AVG' WHERE parameter_id = 4002;
UPDATE parameter SET aggregation_type = 'AVG' WHERE parameter_id = 4003;
UPDATE parameter SET aggregation_type = 'MAX' WHERE parameter_id = 4004;
UPDATE parameter SET aggregation_type = 'MIN' WHERE parameter_id = 4005;
UPDATE parameter SET aggregation_type = 'AVG' WHERE parameter_id = 4011;
UPDATE parameter SET aggregation_type = 'AVG' WHERE parameter_id = 4012;
UPDATE parameter SET aggregation_type = 'AVG' WHERE parameter_id = 4013;
UPDATE parameter SET aggregation_type = 'MAX' WHERE parameter_id = 4014;
UPDATE parameter SET aggregation_type = 'MIN' WHERE parameter_id = 4015;
UPDATE parameter SET aggregation_type = 'SUM' WHERE parameter_id = 5001;
