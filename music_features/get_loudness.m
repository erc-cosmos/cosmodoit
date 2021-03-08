function [L] = get_loudness(inputPath, options)
% Get loudness - Compute Global Loudness of Audio Files
%  [L] = get_loudness(inputPath, options)
%  INPUT ARGUMENTS
%  inputPath       : string; folder path or wav audio file path
%  columns         : string; which column - 'all' (default), 'raw', 'norm', 'smooth', 'envelope'
%  exportLoudness  : boolean; export as csv (true by default)
%  plotLoudness    : boolean; plot results (false by default)
%  smoothSpan      : double; number of data points for calculating the smooth curve (0.03 by default)
%  noNegative      : boolean; set L(i) < 0 = 0 (true by default)
%  OUTPUT ARGUMENTS
%  L               : array; Time (:,1) Loudness (:,2), Normalized (:,3), Normalized-smoothed (:,4), Normalized-envelope (:,5)

    arguments
        inputPath
        options.columns (1,1) string = "all"
        options.export = true
        options.plot   = false
        options.smoothSpan {mustBeNumeric} = 0.03
        options.noNegative = true
    end

    if isfile(inputPath)
        audioFile = inputPath;
        [L] = compute_loudness(audioFile, options.columns, options.export, options.plot, options.smoothSpan, options.noNegative);
    elseif isfolder(inputPath) % get loudness on every .wav file on a folder
        files_list = dir(fullfile(inputPath,"*.wav"));
        for idx = 1:length(files_list)
            audioFile = fullfile(files_list(idx).folder, files_list(idx).name);
            [L] = compute_loudness(audioFile, options.columns, options.export, options.plot, options.smoothSpan, options.noNegative);
        end
    else
        disp('Error: Incorrect input path')
    end

    % Clear L if there are no output arguments
    if nargout==0
       clearvars L
    end

    function [L] = compute_loudness(audioFile, columns, exportLoudness, plotLoudness, smoothSpan, noNegative)
        % Read audio
        [audio, p.fs] = audioread(audioFile); % sampling rate as p.fs for ma_sone
        if size(audio, 2)==2                  % if audio is stereo then convert to mono
            audio = mean(audio,2);
        end

        % Compute loudness using MA Toolbox
        [~, L, ~]  = ma_sone(audio, p);
        L(:,3)     = normalize(L(:,2), 'range');          % Normalized data with range [0 1]
        L(:,4)     = smooth(L(:,3), smoothSpan, 'loess'); % 2nd degree polynomial smooth
        [L(:,5),~] = envelope(L(:,3),floor(length(L(:,1))/L(end,1)),'peak'); % upper peak envelope

        % Remove values below zero
        if noNegative
            L(:,4) = clipNegative(L(:,4));
            L(:,5) = clipNegative(L(:,5));
        end

        % Optional plot
        if plotLoudness
            figure('Name','Loudness','NumberTitle','off');
            colororder({'k','k'})
            plot(L(:,1), L(:,2), 'LineStyle', '-',  'LineWidth', 0.8, 'Color', [0   0 180]/255)
            ylabel('Loudness (sone)', 'FontSize', 14)
            xlabel('Time (s)', 'FontSize', 14)
            yyaxis right
            hold on
            plot(L(:,1), L(:,3), 'LineStyle', '-.', 'LineWidth', 0.2, 'Color', [255 160 0]/255)
            plot(L(:,1), L(:,4), 'LineStyle', '-',  'LineWidth', 3.8, 'Color', [139 0   0]/255)
            plot(L(:,1), L(:,5), 'LineStyle', '--', 'LineWidth', 1.5, 'Color', [0.5 0.5 0.5])
            ylabel('Normalized Loudness (sone)', 'FontSize', 14)
            xlim([L(1,1) L(end,1)])
            ylim([0 1])
            legend('original', 'normalized', 'smoothed', 'envelope')
        end

        % Export
        if exportLoudness
            [fpath, fname, ~]   = fileparts(audioFile);
            N                   = length(L);
            varNames            = {'Time', 'Loudness', 'Loudness_norm', 'Loudness_smooth', 'Loudness_envelope'};
            varTypes            = {'double','double', 'double', 'double', 'double'};
            T                   = table('Size',[N length(varTypes)],'VariableTypes', varTypes, 'VariableNames', varNames);
            T.Time              = L(:,1);
            T.Loudness          = L(:,2);
            T.Loudness_norm     = L(:,3);
            T.Loudness_smooth   = L(:,4);
            T.Loudness_envelope = L(:,5);
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
                T_cols = removevars(T,{'Loudness_norm','Loudness_smooth', 'Loudness_envelope'});
            elseif strcmp(cols,'norm')
                T_cols = removevars(T,{'Loudness','Loudness_smooth', 'Loudness_envelope'});
            elseif strcmp(cols,'smooth')
                T_cols = removevars(T,{'Loudness','Loudness_norm', 'Loudness_envelope'});
            elseif strcmp(cols,'envelope')
                T_cols = removevars(T,{'Loudness','Loudness_norm', 'Loudness_smooth'});
            end    
        end
        function y = clipNegative(x)
            x(x<0) = 0;
            y = x;
        end
    end
end