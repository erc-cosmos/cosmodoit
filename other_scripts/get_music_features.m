

% Save table
% writetable(table_tension, fullfile(save_file_path, '2020-03-12_EC_Chopin_Ballade_N2_Take_2_Tension.csv'))

%% Tension
piece_tension = 'Chopin';
tension_path = '/Users/bedoya/Nextcloud/Documents/Cardiac_response_to_live_music/analysis/tension/Chopin';
beats_v    = beats_v(1:end-1);
T_centroid = load(fullfile(tension_path, strcat(piece_tension,'_centroid.data')));
T_diameter = load(fullfile(tension_path, strcat(piece_tension,'_diameter.data')));
T_key      = load(fullfile(tension_path, strcat(piece_tension,'_key.data')));
T_centroid = [nan; T_centroid(:,2)];
T_diameter = T_diameter(:,2);
T_key      = T_key(:,2);

N = length(T_diameter);
varNames = {'Time', 'cloud_momentum', 'cloud_diameter', 'tensile_strain'};
varTypes = {'double', 'double','double','double'};
table_tension = table('Size',[N 4],'VariableTypes', varTypes, 'VariableNames', varNames);

table_tension.Time           = beats_v;
table_tension.cloud_momentum = T_centroid;
table_tension.cloud_diameter = T_diameter;
table_tension.tensile_strain = T_key;

% Save table
% writetable(table_tension, fullfile(save_file_path, '2020-03-12_EC_Chopin_Ballade_N2_Take_2_Tension.csv'))