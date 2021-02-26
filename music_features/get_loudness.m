function [L] = get_loudness(input_path, columns, export_loudness, plot_loudness)
% Get loudness - Compute Global Loudness of Audio Files
%  [L] = get_loudness(audio_file, plot_loudness)
%  input_path      : folder path or wav audio file path
%  columns         : string; which column - 'all', 'raw', 'norm', 'smooth'
%  export_loudness : boolean; export as csv
%  plot_loudness   : boolean; plot results
%  L               : array; Time (:,1) Loudness (:,2), Normalized (:,3), Normalized-smoothed (:,4)

if nargin < 2 % Export all columns by default
    columns = 'all';
end
if nargin < 3 % Export by default
    export_loudness = true;
end
if nargin < 4 % Do not Plot by default
    plot_loudness = false;
end

if isfile(input_path)
    audio_file = input_path;
    [L] = compute_loudness(audio_file, columns, export_loudness, plot_loudness);
elseif isfolder(input_path)
    files_list = dir(fullfile(input_path,"*.wav"));
    for idx = 1:length(files_list)
        audio_file = fullfile(files_list(idx).folder, files_list(idx).name);
        [L] = compute_loudness(audio_file, columns, export_loudness, plot_loudness);
    end
else
    disp('Error: Incorrect input path')
end

% Clear L if there are no output arguments
if nargout==0
   clearvars L
end

    function [L] = compute_loudness(audio_file, columns, export_loudness, plot_loudness)
    % Read audio
    [audio, p.fs] = audioread(audio_file); % sampling rate as p.fs for ma_sone
    if size(audio, 2)==2 % if audio is stereo then convert to mono
        audio = mean(audio,2);
    end
   
    % Compute loudness using MA Toolbox
    [~, L, ~] = ma_sone(audio, p);
    L(:,3)    = normalize(L(:,2), 'range'); % Normalized data
    L(:,4)    = smooth(L(:,3), 0.03, 'loess'); % 2nd degree polynomial smooth with 3% of samples

    % Optional plot
    if plot_loudness
        figure('Name','Loudness','NumberTitle','off');
        colororder({'k','k'})
        plot(L(:,1), L(:,2), 'LineStyle', '-',  'LineWidth', 0.8, 'Color', [0   0 180]/255)
        ylabel('Loudness (sone)')
        xlabel('Time (s)')
        yyaxis right
        hold on
        plot(L(:,1), L(:,3), 'LineStyle', '-.', 'LineWidth', 0.2, 'Color', [255 160 0]/255)
        plot(L(:,1), L(:,4), 'LineStyle', '-',  'LineWidth', 3.8, 'Color', [139 0   0]/255)
        ylabel('Normalized Loudness (sone)')
        xlim([L(1,1) L(end,1)])
        ylim([0 1])
        legend('original', 'normalized', 'smoothed')
    end

    % Export
    if export_loudness
        [fpath, fname, ~] = fileparts(audio_file);
        N                 = length(L);
        varNames          = {'Time', 'Loudness', 'Loudness_norm', 'Loudness_smooth'};
        varTypes          = {'double','double', 'double', 'double'};
        T                 = table('Size',[N 4],'VariableTypes', varTypes, 'VariableNames', varNames);
        T.Time            = L(:,1);
        T.Loudness        = L(:,2);
        T.Loudness_norm   = L(:,3);
        T.Loudness_smooth = L(:,4);
        % Save table
        table_name        = strcat(fname, '_loudness','.csv');
        table_exp         = fullfile(fpath, table_name);
        T_cols            = assign_columns(T, columns); % only export selected columns
        writetable(T_cols, table_exp)
        if isfile(table_exp)
            disp(strcat("Exported ", columns, " to: ", table_exp))
        end
    end


    function [T_cols] = assign_columns(T, cols)
        if strcmp(cols,'all')
            T_cols = T;
        elseif strcmp(cols,'raw')
            T_cols = removevars(T,{'Loudness_norm','Loudness_smooth'});
        elseif strcmp(cols,'norm')
            T_cols = removevars(T,{'Loudness','Loudness_smooth'});
        elseif strcmp(cols,'smooth')
            T_cols = removevars(T,{'Loudness','Loudness_norm'});
        end    
    end
    end
end